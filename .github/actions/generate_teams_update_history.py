"""Builds latest_raw_files/teams_update_history.{xml,json,yaml} from Microsoft's Teams app
versioning page. Nine platforms are tracked (new and classic Teams for Mac across the public
and government clouds, plus Teams for iOS), each as a list of releases, newest first.
Source: https://learn.microsoft.com/en-us/officeupdates/teams-app-versioning
"""
import json
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from xml.dom import minidom

import pytz
import requests
import yaml
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%B %d, %Y %I:%M %p")

URL = "https://learn.microsoft.com/en-us/officeupdates/teams-app-versioning"
OUT = "latest_raw_files/teams_update_history"
MAC_PKG = "https://statics.teams.cdn.office.net/production-osx/{version}/MicrosoftTeams.pkg"

# platform id -> (name, cloud, heading path that leads to its table, whether it is a Mac pkg we can link)
# The heading path is matched against the h2 > h3 > h4 context the table sits under.
PLATFORMS = [
    ("mac",              "New Teams for Mac",             "Public",     ("Public cloud offerings", "New Teams app version", "Mac"),          True),
    ("ios",              "Teams for iOS",                 "Public",     ("Public cloud offerings", "Classic Teams app version", "Mobile: iOS"), False),
    ("classic_mac",      "Classic Teams for Mac",         "Public",     ("Public cloud offerings", "Classic Teams app version", None),          False),
    ("mac_gcc",          "New Teams for Mac (GCC)",       "Government", ("Government cloud offerings", "New Teams app version", "Mac (GCC)"),   True),
    ("mac_gcch",         "New Teams for Mac (GCCH)",      "Government", ("Government cloud offerings", "New Teams app version", "Mac (GCCH)"),  True),
    ("mac_dod",          "New Teams for Mac (DoD)",       "Government", ("Government cloud offerings", "New Teams app version", "Mac (DoD)"),   True),
    ("classic_mac_gcc",  "Classic Teams for Mac (GCC)",   "Government", ("Government cloud offerings", "Classic Teams app version", "Mac (GCC)"),  False),
    ("classic_mac_gcch", "Classic Teams for Mac (GCCH)",  "Government", ("Government cloud offerings", "Classic Teams app version", "Mac (GCCH)"), False),
    ("classic_mac_dod",  "Classic Teams for Mac (DoD)",   "Government", ("Government cloud offerings", "Classic Teams app version", "Mac (DoD)"),  False),
]


def tables_with_context(soup):
    """Yield (h2, h3, h4, table) for every table, using the headings that precede it."""
    ctx = {"h2": None, "h3": None, "h4": None}
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name == "table":
            yield ctx["h2"], ctx["h3"], ctx["h4"], el
        else:
            ctx[el.name] = el.get_text(" ", strip=True)
            if el.name == "h2":
                ctx["h3"] = ctx["h4"] = None
            elif el.name == "h3":
                ctx["h4"] = None


def find_table(soup, path):
    h2, h3, h4 = path
    for t2, t3, t4, table in tables_with_context(soup):
        if t2 == h2 and t3 == h3 and (t4 == h4 if h4 is not None else t4 is None):
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            if headers[:3] == ["Release year", "Release date", "Teams version"]:
                return table, headers
    return None, None


def parse_table(table, headers):
    releases = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(" ", strip=True).replace("\xa0", " ") for td in tr.find_all("td")]
        if len(cells) < 3:
            continue
        row = dict(zip(headers, cells))
        year, raw_date, version = row["Release year"], row["Release date"], row["Teams version"]
        rolling = "rolling out" in raw_date.lower()
        date_txt = re.sub(r"\s*\(.*?\)\s*", "", raw_date).strip()
        try:  # normalise "October 7" -> "October 07, 2026"
            d = datetime.strptime(f"{date_txt} {year}", "%B %d %Y")
            date = d.strftime("%B %d, %Y")
        except ValueError:
            date = f"{date_txt}, {year}"
        rel = {"date": date, "version": version}
        if row.get("SlimCore version"):
            rel["slimcore_version"] = row["SlimCore version"]
        if row.get("Electron version"):
            rel["electron_version"] = row["Electron version"]
        rel["rolling_out"] = "true" if rolling else "false"
        releases.append(rel)
    return releases


def check_archived(url, timeout=10):
    """True when Microsoft no longer serves the package."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        return r.status_code >= 400
    except requests.RequestException:
        return False


def build():
    logging.info("Fetching %s", URL)
    html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (MOFA feed builder)"}, timeout=60)
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")

    platforms = []
    for pid, name, cloud, path, is_pkg in PLATFORMS:
        table, headers = find_table(soup, path)
        if table is None:
            logging.error("Table not found for %s (%s)", pid, " > ".join(p or "-" for p in path))
            continue
        releases = parse_table(table, headers)
        if is_pkg:
            for rel in releases:
                rel["installer_download"] = MAC_PKG.format(version=rel["version"])
            with ThreadPoolExecutor(max_workers=12) as pool:
                flags = list(pool.map(lambda r: check_archived(r["installer_download"]), releases))
            for rel, archived in zip(releases, flags):
                rel["archive"] = "true" if archived else "false"
        platforms.append({"id": pid, "name": name, "cloud": cloud, "releases": releases})
        logging.info("%-18s %3d releases", pid, len(releases))
    return platforms


def write_outputs(platforms):
    scanned = datetime.now(pytz.timezone("US/Eastern")).strftime("%B %d, %Y %I:%M %p %Z")

    root = ET.Element("Releases")
    ET.SubElement(root, "last_scan_date").text = scanned
    for p in platforms:
        pel = ET.SubElement(root, "platform", id=p["id"], name=p["name"], cloud=p["cloud"])
        for rel in p["releases"]:
            rel_el = ET.SubElement(pel, "release")
            for k, v in rel.items():
                ET.SubElement(rel_el, k).text = v
    pretty = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
    with open(f"{OUT}.xml", "w", encoding="utf-8") as f:
        f.write(pretty)

    data = {"last_scan_date": scanned}
    for p in platforms:
        data[p["id"]] = {"name": p["name"], "cloud": p["cloud"], "releases": p["releases"]}
    with open(f"{OUT}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    with open(f"{OUT}.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    logging.info("Wrote %s.{xml,json,yaml}", OUT)


if __name__ == "__main__":
    write_outputs(build())
