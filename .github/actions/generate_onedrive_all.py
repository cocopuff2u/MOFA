"""
Generate latest_raw_files/macos_standalone_onedrive_all.{xml,json,yaml}

Reads every OneDrive for Mac update-ring manifest Microsoft publishes
(g.live.com/0USSDMC_W5T/*), the official download fwlinks, and the macOS
table on the OneDrive release-notes page.

Output keeps the original <package> schema (name, short_version,
application_id, application_name, CFBundleVersion, full_update_download,
full_update_sha1, full_update_sha256, last_updated) so update_readme.py and
the website keep working, and adds extra fields alongside:

  build                  4-part build number, e.g. 26.173.0906.0008
  rollout_percent        Throttle from the manifest (100 = fully released)
  min_applicable         oldest installed build this update applies to
  max_applicable         newest installed build this update applies to
  intel_update_download  Intel-only pkg
  intel_update_sha256    Microsoft-published SHA256 of the Intel pkg
  universal_zip_download / universal_zip_sha1
  release_date           from the release-notes page when Microsoft lists it
  fwlink                 the go.microsoft.com link for this ring, if any
  updater                which updater reads this manifest
  source                 manifest URL the data came from
  sha256_source          "microsoft_manifest" or "computed"
  sha256_verified        "true" when a download was hashed and matched

Hashes come from the manifests, so no installer download is needed.
Set ONEDRIVE_VERIFY_DOWNLOAD=true to also download each changed pkg,
compute SHA1 and verify SHA256 against Microsoft's published value.

Set ONEDRIVE_OUTPUT_DIR to write somewhere other than latest_raw_files/.
"""

import base64
import hashlib
import html
import json
import logging
import os
import plistlib
import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime
from xml.dom.minidom import parseString

import pytz
import requests
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MANIFEST_BASE = "https://g.live.com/0USSDMC_W5T/"
RELEASE_NOTES_URL = ("https://support.microsoft.com/en-us/office/"
                     "onedrive-release-notes-845dcf18-f921-435e-bf28-4e24b95e5fc0")
HEADERS = {"User-Agent": "MOFA/1.0 (+https://github.com/cocopuff2u/MOFA)"}
TIMEOUT = 60

# Ring label -> manifests. "in_app" is read by the OneDriveUpdaterDaemon inside
# OneDrive.app; "standalone" is read by the legacy OneDriveStandaloneUpdater
# LaunchAgent. Enterprise is Microsoft's internal name for the Deferred ring.
# MSIT rings are Microsoft-internal dogfood rings; builds are public on the CDN.
RINGS = OrderedDict([
    ("Production Ring", {"in_app": "StandaloneProductManifest", "standalone": "MacODSUProduction",
                         "fwlink": "https://go.microsoft.com/fwlink/?linkid=823060"}),
    ("Deferred Ring",   {"in_app": "StandaloneEnterpriseManifest", "standalone": "MacODSUEnterprise",
                         "fwlink": "https://go.microsoft.com/fwlink/?linkid=861009"}),
    ("Insider Ring",    {"in_app": "StandaloneInsidersManifest", "standalone": "MacODSUInsiders",
                         "fwlink": None}),
    ("MSIT Slow Ring (Preview)", {"in_app": "StandaloneMsitSlowManifest", "standalone": "MacODSUMsitSlow",
                                  "fwlink": None}),
    ("MSIT Fast Ring (Preview)", {"in_app": "StandaloneMsitFastManifest", "standalone": "MacODSUMsitFast",
                                  "fwlink": None}),
])

# fwlinks that are not simply "current build of a ring"
FWLINK_PACKAGES = [
    {"name": "Upcoming Deferred Ring", "url": "https://go.microsoft.com/fwlink/?linkid=861010",
     "note": "Deferred ring build currently rolling out (see release notes target date)"},
    {"name": "Rolling Out (Unknown Use)", "url": "https://go.microsoft.com/fwlink/?linkid=861011",
     "note": "Purpose not documented by Microsoft; historically lags Production by about a week"},
    {"name": "Production Ring (Official Download Link)", "url": "https://go.microsoft.com/fwlink/?linkid=823060",
     "note": "The public 'Download OneDrive for Mac' link; matches the release-notes Production version"},
]

# Per-macOS manifests. The name is the *minimum* macOS a manifest serves: a Mac reads
# the manifest for the highest threshold at or below its own version, so
# MacOS15_0Manifest is what every Mac on macOS 15 or newer is offered. The newest
# threshold that returns content is therefore the live Production ring, and the
# older ones hold the final build for Macs that cannot run the current release.
# StandaloneProductManifest still exists but current clients no longer read it
# (it has sat on the macOS 14 build since April 2026); it is kept as a labelled row.
# Verified against the in-app updater's logs on a macOS 26 Mac, which fetched the
# 15.0 manifest's build rather than StandaloneProductManifest's.
MACOS_THRESHOLDS = ["10.13", "10.15", "12.3", "13.0", "14.4", "15.0"]
# Probed every run (a missing manifest answers 204) so a new threshold is picked up
# as soon as Microsoft publishes one.
MACOS_PROBE = [f"{major}.{minor}" for major in (15, 16, 26, 27) for minor in range(0, 8)]


def macos_manifest(threshold):
    return "MacOS" + threshold.replace(".", "_") + "Manifest"


def version_key(v):
    return [int(x) for x in v.split(".")]


def macos_upper_label(next_threshold):
    """'14.4' -> '14.3', '13.0' -> '12.x', '26.0' -> '15.x' (Apple went 15 -> 26)."""
    major, minor = version_key(next_threshold)
    if minor > 0:
        return f"{major}.{minor - 1}"
    return f"{15 if major == 26 else major - 1}.x"


PACKAGE_ORDER = [
    "Production Ring", "Upcoming Production Ring", "Production Ring (Official Download Link)",
    "Production Ring (Legacy Manifest)",
    "Deferred Ring", "Upcoming Deferred Ring",
    "Insider Ring", "Upcoming Insider Ring",
    "MSIT Slow Ring (Preview)", "Upcoming MSIT Slow Ring (Preview)",
    "MSIT Fast Ring (Preview)", "Upcoming MSIT Fast Ring (Preview)",
    "Rolling Out (Unknown Use)",
    "Production Ring (Standalone Updater)", "Deferred Ring (Standalone Updater)",
    "Insider Ring (Standalone Updater)",
    "MSIT Slow Ring (Standalone Updater)", "MSIT Fast Ring (Standalone Updater)",
]

# Fields the README parser requires on every package, in the original order.
LEGACY_FIELDS = ["name", "short_version", "application_id", "application_name", "CFBundleVersion",
                 "full_update_download", "full_update_sha1", "full_update_sha256", "last_updated"]
EXTRA_FIELDS = ["build", "rollout_percent", "min_applicable", "max_applicable",
                "intel_update_download", "intel_update_sha256",
                "universal_zip_download", "universal_zip_sha1",
                "release_date", "fwlink", "updater", "source", "sha256_source", "sha256_verified", "note"]
ALL_FIELDS = LEGACY_FIELDS + EXTRA_FIELDS


# --------------------------------------------------------------------------- helpers

def now_eastern():
    utc_now = datetime.now(pytz.utc)
    return utc_now.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y %I:%M %p %Z")


def http_get(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def b64_to_hex(value):
    if not value:
        return "N/A"
    try:
        return base64.b64decode(value).hex()
    except Exception:
        return "N/A"


def build_from_url(url):
    m = re.search(r"/(\d{2}\.\d{3}\.\d{4}\.\d{4})/", url or "")
    return m.group(1) if m else None


def short_version(build):
    return ".".join(build.split(".")[:3]) if build else "N/A"


def resolve_fwlink(url):
    """Follow redirects with HEAD and return the final URL."""
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=TIMEOUT)
        return r.url
    except Exception as e:
        logging.error(f"Could not resolve {url}: {e}")
        return None


# --------------------------------------------------------------------------- manifests

def fetch_manifest(name, quiet=False):
    """Return a list of entries (newest first) from one g.live.com manifest.
    quiet=True is for probing manifests that may not exist (Microsoft answers 204)."""
    url = MANIFEST_BASE + name
    try:
        data = http_get(url).content
        if not data:
            if not quiet:
                logging.error(f"Manifest {name} is empty")
            return []
        plist = plistlib.loads(data)
    except Exception as e:
        (logging.debug if quiet else logging.error)(f"Could not read manifest {name}: {e}")
        return []

    entries = []
    for d in plist.get("ManifestArray", []):
        sv = d.get("CFBundleShortVersionString")
        bv = d.get("CFBundleVersion", "")
        if not sv:
            continue
        build = f"{sv}.{bv.split('.')[-1]}" if bv else sv
        universal_pkg = d.get("UniversalPkgBinaryURL") or ""
        intel_pkg = d.get("PkgBinaryURL") or ""
        entries.append({
            "build": build,
            "short_version": sv,
            "rollout_percent": str(int(d.get("Throttle", 100))),
            "min_applicable": d.get("MinApplicable", "N/A"),
            "max_applicable": d.get("MaxApplicable", "N/A"),
            # Prefer the universal pkg; very old manifests only have an Intel pkg
            "full_update_download": universal_pkg or intel_pkg,
            "full_update_sha256": b64_to_hex(d.get("UniversalPkgSha256Hash") if universal_pkg else d.get("PkgSha256Hash")),
            "intel_update_download": intel_pkg or "N/A",
            "intel_update_sha256": b64_to_hex(d.get("PkgSha256Hash")),
            "universal_zip_download": d.get("UniversalBinaryURL", "N/A"),
            "universal_zip_sha1": d.get("UniversalSha1Hash", "N/A"),
            "source": url,
        })
    entries.sort(key=lambda e: e["build"], reverse=True)
    return entries


# --------------------------------------------------------------------------- release notes

def fetch_release_notes():
    """Return (mac_table, dates). mac_table: ring -> {released, rolling_out};
    dates: 4-part build -> 'Month D, YYYY' for the macOS sections."""
    try:
        t = http_get(RELEASE_NOTES_URL).text
    except Exception as e:
        logging.error(f"Could not read release notes: {e}")
        return {}, {}

    def clean(s):
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

    mac_table = {}
    for tb in re.findall(r"<table.*?</table>", t, flags=re.S):
        rows = [[clean(c) for c in re.findall(r"<t[dh].*?</t[dh]>", tr, flags=re.S)]
                for tr in re.findall(r"<tr.*?</tr>", tb, flags=re.S)]
        if any("universal" in " ".join(r).lower() for r in rows):  # the macOS table
            for r in rows[1:]:
                if len(r) >= 3:
                    mac_table[r[0]] = {"released": r[1].split(" (")[0].strip(),
                                       "rolling_out": r[2].strip() or "N/A"}

    dates, section = {}, None
    for _, h in re.findall(r"<(h[1-4])[^>]*>(.*?)</h[1-4]>", t, flags=re.S):
        h = clean(h)
        if h.startswith("macOS") or h.startswith("Windows"):
            section = h
        elif section and section.startswith("macOS"):
            m = re.match(r"(\d{2}\.\d{3}\.\d{4}\.\d{4}) \((.+)\)", h)
            if m:
                dates[m.group(1)] = m.group(2)
    logging.info(f"Release notes: {mac_table}; {len(dates)} dated macOS builds")
    return mac_table, dates


# --------------------------------------------------------------------------- existing data

def load_existing(path):
    existing = {}
    try:
        root = ET.parse(path).getroot()
    except FileNotFoundError:
        logging.warning(f"{path} not found. Starting fresh.")
        return existing
    except Exception as e:
        logging.error(f"Error loading existing data: {e}")
        return existing
    for pkg in root.findall("package"):
        rec = {child.tag: (child.text or "") for child in pkg}
        name = rec.get("name")
        if name:
            # Old files only had a 3-part version; derive build from the URL if possible
            if not rec.get("build"):
                rec["build"] = build_from_url(rec.get("full_update_download")) or rec.get("short_version")
            existing[name] = rec
    return existing


# --------------------------------------------------------------------------- hashing

_download_cache = {}


def hash_download(url):
    """Download a pkg once per run and return (sha1, sha256)."""
    if url in _download_cache:
        return _download_cache[url]
    logging.info(f"Downloading {url} to compute hashes")
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        for chunk in r.iter_content(1024 * 1024):
            sha1.update(chunk)
            sha256.update(chunk)
    _download_cache[url] = (sha1.hexdigest(), sha256.hexdigest())
    return _download_cache[url]


def verify_enabled():
    return os.environ.get("ONEDRIVE_VERIFY_DOWNLOAD", "false").lower() in ("1", "true", "yes")


# --------------------------------------------------------------------------- package assembly

def base_package(name):
    return OrderedDict([
        ("name", name),
        ("short_version", "N/A"),
        ("application_id", "ONDR18"),
        ("application_name", "OneDrive.app"),
        ("CFBundleVersion", "com.microsoft.onedrive"),
        ("full_update_download", "N/A"),
        ("full_update_sha1", "N/A"),
        ("full_update_sha256", "N/A"),
        ("last_updated", "N/A"),
    ] + [(f, "N/A") for f in EXTRA_FIELDS])


def finalize(pkg, existing, now, all_known_builds):
    """Set last_updated based on whether the build changed, carry over SHA1,
    and optionally download+verify."""
    name = pkg["name"]
    old = existing.get(name)
    changed = not old or old.get("build") != pkg["build"]

    if not changed:
        pkg["last_updated"] = old.get("last_updated") or now
        if old.get("full_update_sha1") not in (None, "", "N/A"):
            pkg["full_update_sha1"] = old["full_update_sha1"]
        if old.get("sha256_verified") == "true" and old.get("full_update_sha256") == pkg["full_update_sha256"]:
            pkg["sha256_verified"] = "true"
        logging.info(f"No change for '{name}': still {pkg['build']}")
    else:
        pkg["last_updated"] = now
        logging.info(f"Change for '{name}': {old.get('build') if old else 'new'} -> {pkg['build']}")

    # Reuse a SHA1 computed earlier for the same build under another package name
    if pkg["full_update_sha1"] == "N/A":
        for rec in all_known_builds.values():
            if rec.get("build") == pkg["build"] and rec.get("full_update_download") == pkg["full_update_download"] \
                    and rec.get("full_update_sha1") not in (None, "", "N/A"):
                pkg["full_update_sha1"] = rec["full_update_sha1"]
                break

    if changed and verify_enabled() and pkg["full_update_download"].startswith("http"):
        try:
            sha1, sha256 = hash_download(pkg["full_update_download"])
            pkg["full_update_sha1"] = sha1
            if pkg["full_update_sha256"] == "N/A":
                pkg["full_update_sha256"] = sha256
                pkg["sha256_source"] = "computed"
                pkg["sha256_verified"] = "true"
            elif sha256 == pkg["full_update_sha256"]:
                pkg["sha256_verified"] = "true"
            else:
                pkg["sha256_verified"] = "false"
                logging.error(f"SHA256 mismatch for {name}: manifest {pkg['full_update_sha256']} vs computed {sha256}")
        except Exception as e:
            logging.error(f"Download/verify failed for {name}: {e}")
    return pkg


def package_from_entry(name, entry, updater, fwlink, dates, note="N/A"):
    pkg = base_package(name)
    pkg.update({
        "short_version": entry["short_version"],
        "build": entry["build"],
        "full_update_download": entry["full_update_download"],
        "full_update_sha256": entry["full_update_sha256"],
        "sha256_source": "microsoft_manifest" if entry["full_update_sha256"] != "N/A" else "N/A",
        "rollout_percent": entry["rollout_percent"],
        "min_applicable": entry["min_applicable"],
        "max_applicable": entry["max_applicable"],
        "intel_update_download": entry["intel_update_download"],
        "intel_update_sha256": entry["intel_update_sha256"],
        "universal_zip_download": entry["universal_zip_download"],
        "universal_zip_sha1": entry["universal_zip_sha1"],
        "release_date": dates.get(entry["build"], "N/A"),
        "fwlink": fwlink or "N/A",
        "updater": updater,
        "source": entry["source"],
        "note": note,
    })
    return pkg


def build_packages(existing, now):
    mac_table, dates = fetch_release_notes()
    packages = []
    builds_seen = {}  # build -> entry, for fwlink hash reuse

    # Per-macOS manifests, oldest threshold first. The newest one that exists is the
    # live Production ring (see MACOS_THRESHOLDS above).
    macos_entries = OrderedDict()
    for t in sorted(set(MACOS_THRESHOLDS + MACOS_PROBE), key=version_key):
        entries = fetch_manifest(macos_manifest(t), quiet=t not in MACOS_THRESHOLDS)
        if entries:
            macos_entries[t] = entries
            for e in entries:
                builds_seen.setdefault(e["build"], e)
    production_threshold = next(reversed(macos_entries)) if macos_entries else None
    if production_threshold and production_threshold not in MACOS_THRESHOLDS:
        logging.warning(f"New per-macOS manifest found: {macos_manifest(production_threshold)}; add it to MACOS_THRESHOLDS")

    for ring, cfg in RINGS.items():
        # In-app updater manifest is the primary row for the ring. Production comes
        # from the newest per-macOS manifest; StandaloneProductManifest is legacy.
        note = "N/A"
        if ring == "Production Ring" and production_threshold:
            entries = macos_entries[production_threshold]
            note = (f"From {macos_manifest(production_threshold)}, the manifest Macs on macOS "
                    f"{production_threshold} and newer read")
        else:
            entries = fetch_manifest(cfg["in_app"])
        if entries:
            current = next((e for e in entries if e["rollout_percent"] == "100"), entries[-1])
            packages.append(package_from_entry(ring, current, "OneDrive.app in-app updater", cfg["fwlink"], dates, note=note))
            for e in entries:
                builds_seen[e["build"]] = e
                if e is not current and e["build"] > current["build"]:
                    packages.append(package_from_entry(
                        f"Upcoming {ring}", e, "OneDrive.app in-app updater", None, dates,
                        note=f"Staged rollout at {e['rollout_percent']}% of devices"))
        else:
            logging.error(f"No entries in {cfg['in_app']}")

        if ring == "Production Ring" and production_threshold:
            legacy = fetch_manifest(cfg["in_app"])
            if legacy:
                packages.append(package_from_entry(
                    "Production Ring (Legacy Manifest)", legacy[0], "OneDrive.app in-app updater", None, dates,
                    note="StandaloneProductManifest. Current clients read the per-macOS manifests instead; "
                         "kept for reference"))

        # Legacy standalone updater manifest
        sa_entries = fetch_manifest(cfg["standalone"])
        if sa_entries:
            e = sa_entries[0]
            builds_seen.setdefault(e["build"], e)
            packages.append(package_from_entry(
                f"{ring.replace(' (Preview)', '')} (Standalone Updater)", e,
                "OneDriveStandaloneUpdater (legacy LaunchAgent)", None, dates))

    # fwlink-based rows
    for item in FWLINK_PACKAGES:
        final = resolve_fwlink(item["url"])
        build = build_from_url(final)
        pkg = base_package(item["name"])
        pkg.update({"fwlink": item["url"], "updater": "N/A", "source": item["url"], "note": item["note"],
                    "full_update_download": final or item["url"],
                    "build": build or "N/A", "short_version": short_version(build)})
        if build and build in builds_seen:
            e = builds_seen[build]
            if e["full_update_download"] == final:
                pkg.update({"full_update_sha256": e["full_update_sha256"], "sha256_source": "microsoft_manifest",
                            "intel_update_download": e["intel_update_download"],
                            "intel_update_sha256": e["intel_update_sha256"],
                            "universal_zip_download": e["universal_zip_download"],
                            "universal_zip_sha1": e["universal_zip_sha1"],
                            "min_applicable": e["min_applicable"], "max_applicable": e["max_applicable"]})
        else:
            # Build not in any current manifest: carry over hashes if the build is unchanged,
            # otherwise compute them (this is the only case that needs a download).
            old = existing.get(item["name"])
            if old and old.get("build") == build and old.get("full_update_sha256") not in (None, "", "N/A"):
                pkg["full_update_sha256"] = old["full_update_sha256"]
                pkg["sha256_source"] = old.get("sha256_source") or "computed"
            elif final:
                try:
                    sha1, sha256 = hash_download(final)
                    pkg.update({"full_update_sha1": sha1, "full_update_sha256": sha256,
                                "sha256_source": "computed", "sha256_verified": "true"})
                except Exception as ex:
                    logging.error(f"Could not hash {final}: {ex}")
        pkg["release_date"] = dates.get(build, "N/A")
        if item["name"] == "Upcoming Deferred Ring" and mac_table.get("Deferred", {}).get("rolling_out") not in (None, "N/A"):
            pkg["note"] = f"{item['note']}. Release notes: {mac_table['Deferred']['rolling_out']}"
        packages.append(pkg)

    # Last supported builds for older macOS: every per-macOS manifest except the newest
    thresholds = list(macos_entries)
    for i, t in enumerate(thresholds[:-1]):
        upper = macos_upper_label(thresholds[i + 1])
        packages.append(package_from_entry(
            f"Last Build for macOS {t} to {upper}", macos_entries[t][0], "OneDrive.app in-app updater", None, dates,
            note=f"Final build offered to Macs on macOS {t} through {upper}; "
                 f"newer macOS reads {macos_manifest(thresholds[i + 1])}"))

    # Order: known names first in PACKAGE_ORDER, then legacy macOS rows in list order
    order = {n: i for i, n in enumerate(PACKAGE_ORDER)}
    packages = [p for _, p in sorted(enumerate(packages), key=lambda ip: order.get(ip[1]["name"], 500 + ip[0]))]

    known = dict(existing)
    for p in packages:
        finalize(p, existing, now, known)
        known[p["name"]] = p
    return packages, mac_table


# --------------------------------------------------------------------------- output

def to_xml(packages, mac_table, now):
    root = ET.Element("latest")
    ET.SubElement(root, "last_updated").text = now

    rn = ET.SubElement(root, "release_notes")
    ET.SubElement(rn, "source").text = RELEASE_NOTES_URL
    for ring in ("Production", "Deferred"):
        v = mac_table.get(ring, {})
        el = ET.SubElement(rn, ring.lower())
        ET.SubElement(el, "released").text = v.get("released", "N/A")
        ET.SubElement(el, "rolling_out").text = v.get("rolling_out", "N/A")

    for p in packages:
        pkg = ET.SubElement(root, "package")
        for f in ALL_FIELDS:
            ET.SubElement(pkg, f).text = str(p.get(f, "N/A"))
    return parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ")


def xml_to_dict(element):
    result = OrderedDict()
    for child in element:
        if len(child):
            child_dict = xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        else:
            result[child.tag] = child.text or ""
    return result


def convert_to_json_yaml(xml_file):
    root = ET.parse(xml_file).getroot()
    data = OrderedDict()
    data[root.tag] = xml_to_dict(root)
    base = os.path.splitext(xml_file)[0]
    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    class OrderedDumper(yaml.SafeDumper):
        pass

    OrderedDumper.add_representer(
        OrderedDict, lambda d, v: d.represent_mapping(yaml.resolver.Resolver.DEFAULT_MAPPING_TAG, v.items()))
    with open(f"{base}.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, Dumper=OrderedDumper)
    logging.info(f"Wrote {base}.json and {base}.yaml")


def main():
    out_dir = os.environ.get("ONEDRIVE_OUTPUT_DIR", "latest_raw_files")
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, "macos_standalone_onedrive_all.xml")
    now = now_eastern()

    existing = load_existing(output_file)
    packages, mac_table = build_packages(existing, now)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(to_xml(packages, mac_table, now))
    logging.info(f"Wrote {output_file} with {len(packages)} packages")
    convert_to_json_yaml(output_file)


if __name__ == "__main__":
    main()
