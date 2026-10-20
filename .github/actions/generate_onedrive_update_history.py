"""
Generate latest_raw_files/macos_standalone_onedrive_update_history.{xml,json,yaml}

An append-only history of every OneDrive for Mac build MOFA has ever seen.
Microsoft only publishes the *current* state of each update ring, so this
file is how the history gets built: each run adds any build that is new and
records which ring(s) it appeared in.

Daily run (no arguments):
  * reads every ring manifest on g.live.com and adds new builds
  * reads the release-notes page for official macOS release dates
  * fills in CDN download URLs and checks they still exist (HEAD only)

One-time seeding (run locally, needs full git history for --seed-git):
  python3 generate_onedrive_update_history.py --seed-git
      walks the git log of macos_standalone_onedrive_all.xml and adds every
      build it ever recorded, dated by the commit that first recorded it
  python3 generate_onedrive_update_history.py --seed-wayback
      pulls archived copies of the release-notes page from the Wayback
      Machine and adds every dated macOS Production/Deferred build
  python3 generate_onedrive_update_history.py --probe-cdn 2026-01-01 2026-10-19
      enumerates daily builds on the CDN by date (build numbers encode the
      date), adding any that exist; ring is "unknown" for these

Per release:
  build, version, release_date (Microsoft's Production ring date, if listed),
  deferred_release_date (Microsoft's Deferred ring date, if listed),
  cdn_published (Last-Modified of the package on Microsoft's CDN, i.e. when the
  file itself was uploaded; revised builds keep the base version number, so this
  can be months after the date in the version),
  first_seen (when MOFA first recorded it), rings (comma list),
  universal_download, universal_sha256, intel_download, intel_sha256,
  download_available (true/false/unknown), sources (comma list)
"""

import argparse
from email.utils import parsedate_to_datetime
import base64
import html
import json
import logging
import os
import plistlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timedelta
from xml.dom.minidom import parseString

import pytz
import requests
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MANIFEST_BASE = "https://g.live.com/0USSDMC_W5T/"
CDN = "https://oneclient.sfx.ms/Mac"
RELEASE_NOTES_URL = ("https://support.microsoft.com/en-us/office/"
                     "onedrive-release-notes-845dcf18-f921-435e-bf28-4e24b95e5fc0")
HEADERS = {"User-Agent": "MOFA/1.0 (+https://github.com/cocopuff2u/MOFA)"}
TIMEOUT = 60
CURRENT_FILE = "latest_raw_files/macos_standalone_onedrive_all.xml"

MANIFESTS = OrderedDict([
    ("StandaloneProductManifest", "Production"),
    ("MacODSUProduction", "Production"),
    ("StandaloneEnterpriseManifest", "Deferred"),
    ("MacODSUEnterprise", "Deferred"),
    ("StandaloneInsidersManifest", "Insiders"),
    ("MacODSUInsiders", "Insiders"),
    ("StandaloneMsitSlowManifest", "MSIT Slow"),
    ("MacODSUMsitSlow", "MSIT Slow"),
    ("StandaloneMsitFastManifest", "MSIT Fast"),
    ("MacODSUMsitFast", "MSIT Fast"),
    ("MacOS10_13Manifest", "Last for macOS below 10.13"),
    ("MacOS10_15Manifest", "Last for macOS below 10.15"),
    ("MacOS12_3Manifest", "Last for macOS below 12.3"),
    ("MacOS13_0Manifest", "Last for macOS below 13.0"),
    ("MacOS14_4Manifest", "Last for macOS below 14.4"),
])

# Old MOFA package names -> ring label
OLD_NAME_TO_RING = {
    "Production Ring": "Production", "Upcoming Production Ring": "Production",
    "Deferred Ring": "Deferred", "Upcoming Deferred  Ring": "Deferred", "Upcoming Deferred Ring": "Deferred",
    "Insider Ring": "Insiders", "Upcoming Insider Ring": "Insiders",
    "Rolling Out (Unknown Use)": "Rolling Out", "App New Version (Unknown Use)": "Production",
    "Production Ring (Official Download Link)": "Production",
    "Production Ring (Legacy Manifest)": "Production",
    "MSIT Slow Ring (Preview)": "MSIT Slow", "Upcoming MSIT Slow Ring (Preview)": "MSIT Slow",
    "MSIT Fast Ring (Preview)": "MSIT Fast", "Upcoming MSIT Fast Ring (Preview)": "MSIT Fast",
}


def ring_for_package_name(name):
    """Ring label for a package name from any version of the current-state feed,
    or None when the name says nothing useful about a ring."""
    name = " ".join(name.split())
    if name in OLD_NAME_TO_RING:
        return OLD_NAME_TO_RING[name]
    base = name.replace(" (Standalone Updater)", "")
    if base in OLD_NAME_TO_RING:
        return OLD_NAME_TO_RING[base]
    m = re.match(r"Last Build for macOS (\d+\.\d+) to ", name)
    if m:
        return f"Last for macOS {m.group(1)}+"
    return None

FIELDS = ["build", "version", "release_date", "deferred_release_date", "cdn_published", "first_seen", "rings",
          "universal_download", "universal_sha256", "intel_download", "intel_sha256",
          "download_available", "sources"]

BUILD_RE = re.compile(r"\b(\d{2}\.\d{3}\.\d{4}\.\d{4})\b")


# --------------------------------------------------------------------------- helpers

def now_eastern():
    return datetime.now(pytz.utc).astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y %I:%M %p %Z")


def today_str():
    return datetime.now(pytz.utc).astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")


def http_get(url, **kw):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


def b64_to_hex(v):
    try:
        return base64.b64decode(v).hex() if v else "N/A"
    except Exception:
        return "N/A"


def clean_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def build_sort_key(b):
    return tuple(int(x) for x in b.split("."))


def add_to_list_field(rec, field, value):
    if not value or value == "N/A":
        return
    items = [x for x in (rec.get(field) or "").split(", ") if x and x != "N/A"]
    if value not in items:
        items.append(value)
    rec[field] = ", ".join(items)


# --------------------------------------------------------------------------- history store

class History:
    def __init__(self, path):
        self.path = path
        self.records = OrderedDict()
        self.load()

    def load(self):
        try:
            root = ET.parse(self.path).getroot()
        except FileNotFoundError:
            logging.warning(f"{self.path} not found; starting a new history")
            return
        for rel in root.findall("release"):
            rec = OrderedDict((f, "N/A") for f in FIELDS)
            for child in rel:
                rec[child.tag] = child.text or "N/A"
            if BUILD_RE.fullmatch(rec["build"] or ""):
                rings = [r for r in (rec.get("rings") or "").split(", ") if r and r not in ("N/A", "unknown")]
                rec["rings"] = ", ".join(rings) or "N/A"
                self.records[rec["build"]] = rec
        logging.info(f"Loaded {len(self.records)} builds from {self.path}")

    def upsert(self, build, ring=None, source=None, first_seen=None, release_date=None, deferred_release_date=None,
               universal_download=None, universal_sha256=None, intel_download=None, intel_sha256=None):
        if not BUILD_RE.fullmatch(build):
            return None
        rec = self.records.get(build)
        new = rec is None
        if new:
            rec = OrderedDict((f, "N/A") for f in FIELDS)
            rec["build"] = build
            rec["version"] = ".".join(build.split(".")[:3])
            rec["first_seen"] = first_seen or today_str()
            self.records[build] = rec
            logging.info(f"New build {build} ({ring or 'unknown'}, via {source})")
        else:
            # Keep the earliest first_seen we know about
            if first_seen:
                try:
                    old = datetime.strptime(rec["first_seen"], "%B %d, %Y")
                    cand = datetime.strptime(first_seen, "%B %d, %Y")
                    if cand < old:
                        rec["first_seen"] = first_seen
                except Exception:
                    pass
        add_to_list_field(rec, "rings", None if ring == "unknown" else ring)
        add_to_list_field(rec, "sources", source)
        if release_date and rec["release_date"] == "N/A":
            rec["release_date"] = release_date
        if deferred_release_date and rec["deferred_release_date"] == "N/A":
            rec["deferred_release_date"] = deferred_release_date
        for k, v in (("universal_download", universal_download), ("universal_sha256", universal_sha256),
                     ("intel_download", intel_download), ("intel_sha256", intel_sha256)):
            if v and v != "N/A" and rec[k] == "N/A":
                rec[k] = v
        return rec

    def save(self, now):
        root = ET.Element("Releases")
        ET.SubElement(root, "last_scan_date").text = now
        ET.SubElement(root, "total_builds").text = str(len(self.records))
        for build in sorted(self.records, key=build_sort_key, reverse=True):
            rec = self.records[build]
            rel = ET.SubElement(root, "release")
            for f in FIELDS:
                ET.SubElement(rel, f).text = rec.get(f, "N/A") or "N/A"
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="    "))
        self._write_json_yaml(root)
        logging.info(f"Saved {len(self.records)} builds to {self.path}")

    def _write_json_yaml(self, root):
        data = OrderedDict()
        data["Releases"] = OrderedDict()
        data["Releases"]["last_scan_date"] = root.find("last_scan_date").text
        data["Releases"]["total_builds"] = root.find("total_builds").text
        data["Releases"]["release"] = [OrderedDict((c.tag, c.text or "") for c in rel) for rel in root.findall("release")]
        base = os.path.splitext(self.path)[0]
        with open(f"{base}.json", "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

        class OrderedDumper(yaml.SafeDumper):
            pass

        OrderedDumper.add_representer(
            OrderedDict, lambda d, v: d.represent_mapping(yaml.resolver.Resolver.DEFAULT_MAPPING_TAG, v.items()))
        with open(f"{base}.yaml", "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, default_flow_style=False, allow_unicode=True, Dumper=OrderedDumper)


# --------------------------------------------------------------------------- sources

def ingest_manifests(hist):
    for name, ring in MANIFESTS.items():
        url = MANIFEST_BASE + name
        try:
            plist = plistlib.loads(http_get(url).content)
        except Exception as e:
            logging.error(f"Could not read {name}: {e}")
            continue
        for d in plist.get("ManifestArray", []):
            sv, bv = d.get("CFBundleShortVersionString"), d.get("CFBundleVersion", "")
            if not sv or not bv:
                continue
            build = f"{sv}.{bv.split('.')[-1]}"
            hist.upsert(build, ring=ring, source=f"manifest:{name}",
                        universal_download=d.get("UniversalPkgBinaryURL"),
                        universal_sha256=b64_to_hex(d.get("UniversalPkgSha256Hash")),
                        intel_download=d.get("PkgBinaryURL"),
                        intel_sha256=b64_to_hex(d.get("PkgSha256Hash")))


def parse_release_notes_html(text, source):
    """Yield (build, ring, release_date) from a copy of the release-notes page."""
    section = None
    for _, h in re.findall(r"<(h[1-4])[^>]*>(.*?)</h[1-4]>", text, flags=re.S):
        h = clean_html(h)
        if h.startswith("macOS") or h.startswith("Windows"):
            section = h
        elif section and section.startswith("macOS"):
            m = re.match(r"(\d{2}\.\d{3}\.\d{4}\.\d{4}) \((.+)\)", h)
            if m:
                ring = "Deferred" if "Deferred" in section else "Production"
                date = m.group(2)
                if date.lower().startswith("target date"):
                    continue  # not released yet
                yield m.group(1), ring, date
    # Older page layouts (pre-2024) listed Mac versions in tables or paragraphs
    # rather than dated headings; pick up plain "Mac ... version" mentions.
    for m in re.finditer(r"Mac[^<]{0,120}?(\d{2}\.\d{3}\.\d{4}\.\d{4})", text):
        yield m.group(1), "Production", None


def ingest_release_notes(hist):
    try:
        text = http_get(RELEASE_NOTES_URL).text
    except Exception as e:
        logging.error(f"Could not read release notes: {e}")
        return
    n = 0
    for build, ring, date in parse_release_notes_html(text, "release_notes"):
        # The page dates a build once per ring: Production first, then Deferred
        # roughly 60 days later. Keep them apart so neither feed shows the wrong one.
        if ring == "Deferred":
            hist.upsert(build, ring=ring, source="release_notes", deferred_release_date=date)
        else:
            hist.upsert(build, ring=ring, source="release_notes", release_date=date)
        n += 1
    logging.info(f"Release notes: {n} macOS builds")


def seed_from_git(hist, repo_root="."):
    """Walk the git history of the old onedrive_all.xml for builds + commit dates."""
    try:
        log = subprocess.run(["git", "log", "--reverse", "--format=%H %ad", "--date=format:%B %d, %Y", "--", CURRENT_FILE],
                             cwd=repo_root, capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception as e:
        logging.error(f"git log failed: {e}")
        return
    commits = [l.split(" ", 1) for l in log if l.strip()]
    logging.info(f"Walking {len(commits)} commits of {CURRENT_FILE}")
    for sha, date in commits:
        xml = subprocess.run(["git", "show", f"{sha}:{CURRENT_FILE}"], cwd=repo_root,
                             capture_output=True, text=True).stdout
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for pkg in root.findall("package"):
            name = (pkg.findtext("name") or "").strip()
            url = pkg.findtext("full_update_download") or ""
            build = (pkg.findtext("build") or "").strip()
            if not BUILD_RE.fullmatch(build):
                m = BUILD_RE.search(url)
                build = m.group(1) if m else None
            if not build:
                continue
            ring = ring_for_package_name(name)
            sha256 = (pkg.findtext("full_update_sha256") or "").strip()
            universal = url if "/universal/" in url else None
            intel = url if url.startswith(CDN) and "/universal/" not in url else None
            hist.upsert(build, ring=ring, source="mofa_git_history", first_seen=date,
                        universal_download=universal, universal_sha256=sha256 if universal else None,
                        intel_download=intel, intel_sha256=sha256 if intel else None)


def seed_from_wayback(hist):
    cdx = ("https://web.archive.org/cdx/search/cdx?url=" + RELEASE_NOTES_URL.split("://", 1)[1]
           + "&output=json&fl=timestamp&collapse=timestamp:6&limit=5000")
    try:
        rows = http_get(cdx).json()[1:]
    except Exception as e:
        logging.error(f"Wayback CDX failed: {e}")
        return
    logging.info(f"Wayback: {len(rows)} monthly snapshots of the release notes")
    # Wayback rate-limits aggressively (about 15 requests a minute, then it
    # refuses connections for a while). Go newest-first so the most useful
    # snapshots land first, pause between fetches, and give up after a run of
    # failures rather than hammering it. Re-run later to pick up the rest;
    # builds already recorded are simply updated, never duplicated.
    consecutive_failures = 0
    for (ts,) in reversed(rows):
        snap = f"https://web.archive.org/web/{ts}id_/{RELEASE_NOTES_URL}"
        text = None
        for attempt in range(3):
            try:
                text = http_get(snap).text
                break
            except Exception as e:
                logging.warning(f"Snapshot {ts} attempt {attempt + 1} failed: {e}")
                time.sleep(20 * (attempt + 1))
        if text is None:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                logging.error("Wayback keeps refusing; stopping. Re-run --seed-wayback later for the rest.")
                break
            continue
        consecutive_failures = 0
        snap_date = datetime.strptime(ts[:8], "%Y%m%d").strftime("%B %d, %Y")
        n = 0
        for build, ring, date in parse_release_notes_html(text, f"wayback:{ts}"):
            hist.upsert(build, ring=ring, source="release_notes_wayback", release_date=date, first_seen=snap_date)
            n += 1
        logging.info(f"Snapshot {ts}: {n} macOS builds")
        time.sleep(6)


def cdn_head(url):
    """(exists, published) for a CDN URL; published is 'Month D, YYYY' from Last-Modified or None."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        ok = r.status_code == 200 and int(r.headers.get("Content-Length", "0")) > 1_000_000
        lm = r.headers.get("Last-Modified")
        published = parsedate_to_datetime(lm).strftime("%B %d, %Y").replace(" 0", " ") if ok and lm else None
        return ok, published
    except Exception:
        return False, None


def cdn_url_exists(url):
    return cdn_head(url)[0]


def fill_cdn_urls(hist, check_all=False):
    """Construct CDN URLs for builds that lack them and HEAD-check availability."""
    for build, rec in hist.records.items():
        if rec["download_available"] != "N/A" and not check_all:
            continue
        candidates = []
        if rec["universal_download"] == "N/A":
            candidates.append(("universal_download", f"{CDN}/Installers/{build}/universal/OneDrive.pkg"))
        if rec["intel_download"] == "N/A":
            candidates.append(("intel_download", f"{CDN}/Installers/{build}/OneDrive.pkg"))
            candidates.append(("intel_download", f"{CDN}/Prod/{build}/OneDrive.pkg"))
        available = False
        for field, url in candidates:
            if rec[field] != "N/A":
                continue
            ok, published = cdn_head(url)
            if ok:
                rec[field] = url
                available = True
                if published and rec["cdn_published"] == "N/A":
                    rec["cdn_published"] = published
        for field in ("universal_download", "intel_download"):
            if rec[field] != "N/A" and not available:
                available, published = cdn_head(rec[field])
                if published and rec["cdn_published"] == "N/A":
                    rec["cdn_published"] = published
        rec["download_available"] = "true" if available else "false"

    # Upload date for builds checked before this field existed: one HEAD each, once.
    for build, rec in hist.records.items():
        if rec["cdn_published"] != "N/A" or rec["download_available"] != "true":
            continue
        url = rec["universal_download"] if rec["universal_download"] != "N/A" else rec["intel_download"]
        if url != "N/A":
            _, published = cdn_head(url)
            if published:
                rec["cdn_published"] = published


def probe_cdn(hist, start, end, max_suffix=12):
    """Build numbers are YY.DDD.MMDD.NNNN with DDD = day of year. Enumerate each
    day in [start, end] and try suffixes 0001.. until one is missing."""
    day = start
    found = 0
    while day <= end:
        yy, ddd, mmdd = day.strftime("%y"), day.strftime("%j"), day.strftime("%m%d")
        for n in range(1, max_suffix + 1):
            build = f"{yy}.{ddd}.{mmdd}.{n:04d}"
            if build in hist.records:
                continue
            uni = f"{CDN}/Installers/{build}/universal/OneDrive.pkg"
            intel = f"{CDN}/Installers/{build}/OneDrive.pkg"
            if cdn_url_exists(uni):
                hist.upsert(build, ring="unknown", source="cdn_probe", universal_download=uni,
                            intel_download=intel if cdn_url_exists(intel) else None)
                hist.records[build]["download_available"] = "true"
                found += 1
            elif cdn_url_exists(intel):
                hist.upsert(build, ring="unknown", source="cdn_probe", intel_download=intel)
                hist.records[build]["download_available"] = "true"
                found += 1
            else:
                break
        day += timedelta(days=1)
    logging.info(f"CDN probe found {found} new builds")


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-git", action="store_true", help="seed from the git history of the current-state XML")
    ap.add_argument("--seed-wayback", action="store_true", help="seed from Wayback Machine copies of the release notes")
    ap.add_argument("--probe-cdn", nargs=2, metavar=("START", "END"), help="enumerate CDN builds between two YYYY-MM-DD dates")
    ap.add_argument("--recheck-downloads", action="store_true", help="re-HEAD every stored download URL")
    ap.add_argument("--output-dir", default=os.environ.get("ONEDRIVE_OUTPUT_DIR", "latest_raw_files"))
    args = ap.parse_args()

    hist = History(os.path.join(args.output_dir, "macos_standalone_onedrive_update_history.xml"))

    if args.seed_git:
        seed_from_git(hist)
    if args.seed_wayback:
        seed_from_wayback(hist)
    ingest_manifests(hist)
    ingest_release_notes(hist)
    if args.probe_cdn:
        start = datetime.strptime(args.probe_cdn[0], "%Y-%m-%d")
        end = datetime.strptime(args.probe_cdn[1], "%Y-%m-%d")
        probe_cdn(hist, start, end)
    fill_cdn_urls(hist, check_all=args.recheck_downloads)
    hist.save(now_eastern())


if __name__ == "__main__":
    sys.exit(main())
