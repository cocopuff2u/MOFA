#!/usr/bin/env python3
"""
Generate latest_raw_files/macos_other_latest.{xml,yaml,json}

The home for Microsoft's "other" macOS offerings -- the dev and admin tools that
live outside the Office/Microsoft AutoUpdate world and therefore don't fit the
standalone/MAU scripts. Think PowerShell, the .NET SDK, Azure CLI, Bicep,
AzCopy, and friends: scattered across GitHub releases, the .NET release feed,
and Homebrew, each with its own quirks for finding "what's the latest."

This script normalizes that mess into the same schema as the other macOS feeds.
Every app declares a `source`, and the matching fetcher knows how to resolve the
current version, release date, and macOS download(s):

  - github_release : newest GitHub release; pick the macOS asset(s) by name match
  - dotnet         : the official .NET release-metadata index (per channel)
  - homebrew       : the Homebrew formula API (version + date via the upstream tag;
                     no single installer, so the install is `brew install <formula>`)

macOS-only by design: GitHub assets are matched on osx/darwin, and the Homebrew
tools are mac-installable. Apple Silicon (arm64) is preferred, Intel (x64) is the
fallback. SHA1/SHA256 are computed for real downloads in a single pass.

Set MOFA_SKIP_SHA=true for a fast local run that skips package hashing, and set
GITHUB_TOKEN to lift the GitHub API rate limit (60/hr -> 5000/hr) in CI.
"""

import os
import re
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from hashlib import sha1, sha256
from xml.dom import minidom

import requests
import yaml
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%B %d, %Y %I:%M %p',
)

REQUEST_TIMEOUT = (10, 120)  # (connect, read) seconds
SKIP_SHA = os.environ.get("MOFA_SKIP_SHA", "false").lower() in ("1", "true", "yes")
OUTPUT_BASE = "latest_raw_files/macos_other_latest"

# A GitHub token (if provided) raises the API rate limit from 60 to 5000/hr.
GITHUB_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "MOFA-other"}
if os.environ.get("GITHUB_TOKEN"):
    GITHUB_HEADERS["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"

# Field order mirrors the existing macOS feeds (beta/preview schema) so this feed
# is a drop-in sibling for any downstream tooling (README/RSS generators, etc.).
FIELD_ORDER = [
    "name", "application_id", "application_name", "CFBundleVersion",
    "short_version", "full_version", "last_updated", "min_os",
    "update_download", "latest_download", "sha1", "sha256",
]


def now_eastern():
    return datetime.now(pytz.utc).astimezone(pytz.timezone('US/Eastern')).strftime('%B %d, %Y %I:%M %p %Z')


def fmt_date(iso):
    if not iso:
        return "N/A"
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00')).strftime('%B %d, %Y')
    except Exception:
        return iso


def http_json(url, headers=None):
    r = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers or {"User-Agent": "MOFA-other"})
    r.raise_for_status()
    return r.json()


def compute_hashes(url):
    """Download once and compute SHA1 + SHA256 in one pass (matches the other
    feeds, which carry both). Returns ('N/A','N/A') on skip / no URL / failure."""
    if SKIP_SHA or not url or not str(url).startswith("http"):
        return "N/A", "N/A"
    try:
        logging.info(f"Hashing {url}...")
        h1, h256 = sha1(), sha256()
        with requests.get(url, stream=True, allow_redirects=True, timeout=REQUEST_TIMEOUT) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1 << 20):
                h1.update(chunk)
                h256.update(chunk)
        return h1.hexdigest(), h256.hexdigest()
    except Exception as e:
        logging.error(f"Hashing failed for {url}: {e}")
        return "N/A", "N/A"


# --------------------------------------------------------------------------- #
# Source fetchers -- each returns a partial record (no name/hashes yet).
# --------------------------------------------------------------------------- #
def _pick_asset(assets, include, exclude=()):
    """First asset whose lowercased name contains all `include` and no `exclude`."""
    for name, url in assets.items():
        low = name.lower()
        if all(p in low for p in include) and not any(p in low for p in exclude):
            return url
    return "N/A"


def from_github_release(cfg):
    d = http_json(f"https://api.github.com/repos/{cfg['repo']}/releases/latest", GITHUB_HEADERS)
    assets = {a['name']: a['browser_download_url'] for a in d.get('assets', [])}
    ex = cfg.get('exclude', [])
    tag = d.get('tag_name', '') or ''
    m = re.search(r'\d[\d.]*\d|\d', tag)  # pull the version out of tags like 'azure-dev-cli_1.25.6'
    return {
        "version": m.group(0) if m else (tag or "N/A"),
        "release_date": fmt_date(d.get('published_at')),
        "install_method": cfg.get('install_method', 'pkg'),
        "download_arm64": _pick_asset(assets, cfg.get('arm64', []), ex) if cfg.get('arm64') else "N/A",
        "download_x64": _pick_asset(assets, cfg.get('x64', []), ex) if cfg.get('x64') else "N/A",
        "homepage": d.get('html_url', cfg.get('homepage', 'N/A')),
    }


def from_dotnet(cfg):
    idx = http_json("https://dotnetcli.blob.core.windows.net/dotnet/release-metadata/releases-index.json")
    want = cfg.get('channel', 'LTS')  # "LTS" / "STS" / or a channel-version like "10.0"
    chan = next((c for c in idx['releases-index']
                 if want in (c['channel-version'], c['release-type'].upper(), c['support-phase'].upper())), None)
    chan = chan or idx['releases-index'][0]
    detail = http_json(chan['releases.json'])
    rel = detail['releases'][0]
    sdk = rel['sdk']
    files = {f.get('name', '').lower(): f.get('url', '') for f in sdk.get('files', [])}
    return {
        "version": sdk.get('version', 'N/A'),
        "release_date": fmt_date(rel.get('release-date')),
        "install_method": "pkg",
        "download_arm64": next((u for n, u in files.items() if n.endswith('.pkg') and 'osx' in n and 'arm64' in n), "N/A"),
        "download_x64": next((u for n, u in files.items() if n.endswith('.pkg') and 'osx' in n and 'x64' in n), "N/A"),
        "homepage": "https://dotnet.microsoft.com/download",
    }


def from_homebrew(cfg):
    d = http_json(f"https://formulae.brew.sh/api/formula/{cfg['formula']}.json")
    # Homebrew has no per-version release date, but the stable source URL points at
    # the upstream GitHub tag -- pull the published date from that release.
    date = "N/A"
    src = d.get('urls', {}).get('stable', {}).get('url', '')
    m = re.search(r'github\.com/([^/]+)/([^/]+)/archive/refs/tags/(.+)\.tar\.gz', src)
    if m:
        owner, repo, tag = m.group(1), m.group(2), m.group(3)
        try:
            rel = http_json(f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}", GITHUB_HEADERS)
            date = fmt_date(rel.get('published_at'))
        except Exception as e:
            logging.warning(f"{cfg['formula']}: no GitHub release date for tag {tag}: {e}")
    return {
        "version": d['versions']['stable'],
        "release_date": date,
        "install_method": f"brew install {cfg['formula']}",
        "download_arm64": "N/A",
        "download_x64": "N/A",
        "homepage": d.get('homepage', 'N/A'),
    }


FETCHERS = {
    "github_release": from_github_release,
    "dotnet": from_dotnet,
    "homebrew": from_homebrew,
}

# --------------------------------------------------------------------------- #
# App catalog -- add new Microsoft macOS tools here.
# --------------------------------------------------------------------------- #
APPS = {
    "PowerShell": {
        "source": "github_release", "repo": "PowerShell/PowerShell",
        # exclude 'lts' so we get the current stable, not the LTS-tagged pkg
        "arm64": ["osx-arm64", ".pkg"], "x64": ["osx-x64", ".pkg"], "exclude": ["lts"],
        "bundle_id": "com.microsoft.powershell",  # stable pkg/app identifier
    },
    ".NET SDK (LTS)": {
        "source": "dotnet", "channel": "LTS",
    },
    "Azure CLI": {
        "source": "homebrew", "formula": "azure-cli",
    },
    "Azure Functions Core Tools": {
        "source": "github_release", "repo": "Azure/azure-functions-core-tools",
        "arm64": ["osx-arm64"], "x64": ["osx-x64"], "install_method": "zip",
    },
    "Azure Developer CLI (azd)": {
        "source": "github_release", "repo": "Azure/azure-dev",
        "arm64": ["darwin", "arm64"], "x64": ["darwin", "amd64"], "install_method": "zip",
    },
    "AzCopy": {
        "source": "github_release", "repo": "Azure/azure-storage-azcopy",
        "arm64": ["darwin", "arm64"], "x64": ["darwin", "amd64"], "install_method": "zip",
    },
    "Bicep CLI": {
        "source": "github_release", "repo": "Azure/bicep",
        "arm64": ["bicep-osx-arm64"], "x64": ["bicep-osx-x64"], "install_method": "binary",
    },
    "sqlcmd": {
        "source": "homebrew", "formula": "sqlcmd",
    },
    # Azure Data Studio retired by Microsoft (last GitHub release tagged "final") -- omitted.
}


def read_existing(path):
    """Parse a previously generated feed into {name: {field: value}} so apps whose
    version hasn't changed can be reused without re-downloading / re-hashing."""
    if not os.path.exists(path):
        return {}
    try:
        root = ET.parse(path).getroot()
        return {pkg.findtext("name"): {c.tag: (c.text or "N/A") for c in pkg}
                for pkg in root.findall("package") if pkg.findtext("name")}
    except Exception as e:
        logging.warning(f"Could not read existing feed {path}: {e}")
        return {}


def needs_hash_retry(rec):
    """SHA is missing but there's a real download URL -> worth retrying once
    (covers a prior transient hash failure that would otherwise stay N/A forever)."""
    dl = rec.get("latest_download", "")
    return (isinstance(dl, str) and dl.startswith("http")
            and rec.get("sha256", "N/A") in ("N/A", None, ""))


def assemble_record(name, cfg, data):
    """Map fetched source data into the feed schema and compute hashes."""
    # macOS primary download: prefer Apple Silicon (arm64), fall back to Intel (x64).
    primary = data.get("download_arm64")
    if primary in ("N/A", None):
        primary = data.get("download_x64", "N/A")
    has_dl = isinstance(primary, str) and primary.startswith("http")
    sha1v, sha256v = compute_hashes(primary)
    rec = {
        "name": name,
        "application_id": "N/A",            # no MAU App ID for non-MAU tools
        "application_name": name,
        "CFBundleVersion": cfg.get("bundle_id", "N/A"),  # only set where a stable pkg/app id exists
        "short_version": data.get("version", "N/A"),
        "full_version": data.get("version", "N/A"),
        "last_updated": data.get("release_date", "N/A"),
        "min_os": "N/A",
        # Installer apps: both point at the macOS package. Homebrew-only apps have
        # no download URL, so record the install command in both fields (no N/A).
        "update_download": primary if has_dl else data.get("install_method", "N/A"),
        "latest_download": primary if has_dl else data.get("install_method", "N/A"),
        "sha1": sha1v,
        "sha256": sha256v,
    }
    return {k: rec.get(k, "N/A") for k in FIELD_ORDER}


def main():
    last_updated = now_eastern()
    logging.info(f"Run start: {last_updated}")
    existing = read_existing(f"{OUTPUT_BASE}.xml")

    records = []
    for name, cfg in APPS.items():
        logging.info("-" * 50)
        logging.info(f"Checking {name} via {cfg['source']}...")
        try:
            # Cheap step first: resolve version + URLs (no package download yet).
            data = FETCHERS[cfg["source"]](cfg)
            new_ver = data.get("version", "N/A")
            prev = existing.get(name)
            if prev and prev.get("short_version") == new_ver:
                # Version unchanged -> reuse the whole existing record; do NOT re-hash.
                rec = {k: prev.get(k, "N/A") for k in FIELD_ORDER}
                if needs_hash_retry(rec):
                    logging.info(f"{name}: {new_ver} unchanged but SHA missing -- retrying hash only.")
                    h1, h256 = compute_hashes(rec.get("latest_download"))
                    if h1 != "N/A":
                        rec["sha1"], rec["sha256"] = h1, h256
                else:
                    logging.info(f"{name}: {new_ver} unchanged -- reusing existing (no re-hash).")
            else:
                # New app or version changed -> build fresh and hash the package.
                rec = assemble_record(name, cfg, data)
                change = "new" if not prev else f"{prev.get('short_version')} -> {new_ver}"
                logging.info(f"{name}: {new_ver} ({rec['last_updated']}) [{change}]")
            records.append(rec)
        except Exception as e:
            logging.error(f"Failed {name}: {e}")
            if name in existing:
                logging.info(f"Reusing last-known data for {name}.")
                records.append({k: existing[name].get(k, "N/A") for k in FIELD_ORDER})

    os.makedirs(os.path.dirname(OUTPUT_BASE), exist_ok=True)

    # XML
    root = ET.Element("latest")
    ET.SubElement(root, "last_updated").text = last_updated
    for rec in records:
        pkg = ET.SubElement(root, "package")
        for k in FIELD_ORDER:
            ET.SubElement(pkg, k).text = str(rec.get(k, "N/A"))
    xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="    ")
    with open(f"{OUTPUT_BASE}.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    logging.info(f"Wrote {OUTPUT_BASE}.xml")

    # YAML + JSON (same shape)
    payload = {"last_updated": last_updated, "packages": records}
    with open(f"{OUTPUT_BASE}.yaml", "w", encoding="utf-8") as f:
        yaml.dump(payload, f, default_flow_style=False, sort_keys=False)
    with open(f"{OUTPUT_BASE}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
    logging.info(f"Wrote {OUTPUT_BASE}.yaml and .json")


if __name__ == "__main__":
    main()
