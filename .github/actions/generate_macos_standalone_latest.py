import os
import requests
import xml.etree.ElementTree as ET
from hashlib import sha256, sha1
from xml.dom import minidom
import json
from datetime import datetime
import time
import pytz
import re
import yaml
import logging

# Configure logging with a cleaner and more human-readable format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%B %d, %Y %I:%M %p'
)

def get_current_date_time():
    """
    Get the current date and time in Eastern Time.

    Returns:
        str: The formatted date and time.
    """
    # Get current UTC time and convert it to Eastern Time (or any other timezone)
    utc_now = datetime.now(pytz.utc)  # Get current UTC time with tz info
    eastern_time = utc_now.astimezone(pytz.timezone('US/Eastern'))  # Convert to Eastern Time

    # Format the date and time as needed (e.g., 12/06/2024 04:30 PM Eastern)
    formatted_date_time = eastern_time.strftime('%B %d, %Y %I:%M %p %Z')  # 'December 06, 2024 04:30 PM Eastern'

    return formatted_date_time

# Call the function to test it
last_update_date_time = get_current_date_time()
logging.info(f"Current date and time: {last_update_date_time}")

# Define app-specific configurations
apps = {
    "Microsoft Office Suite": {
        "url": "https://officecdnmac.microsoft.com/pr/A1E15C18-4D18-40B0-8577-616A9470BB10/MacAutoUpdate/0409OPIM2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.office",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=525133",
            "application_id": "Data sourced from Outlook (CurrentThrottle)",
            "application_name": "Data sourced from Outlook (CurrentThrottle)",
        },
        "keys": {
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "NA",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Microsoft BusinessPro Suite": {
        "url": "https://officecdnmac.microsoft.com/pr/A1E15C18-4D18-40B0-8577-616A9470BB10/MacAutoUpdate/0409OPIM2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.office",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2009112",
            "application_id": "Data sourced from Outlook (CurrentThrottle)",
            "application_name": "Data sourced from Outlook (CurrentThrottle)",
        },
        "keys": {
           "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "NA",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Word": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSWD2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.word",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=525134",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Excel": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409XCEL2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.excel",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=525135",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "PowerPoint": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409PPT32019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.powerpoint",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=525136",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Outlook": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409OPIM2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.outlook",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2228621",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "OneNote": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409ONMC2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.onenote",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=820886",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    # "OneDrive": { ######## MOVED OVER TO ITS OWN FILE MACOS_STANDALONE_ONEDRIVE_LATEST.* ########
    #     "url": "https://g.live.com/0USSDMC_W5T/MacODSUProduction",
    #     "manual_entries": {
    #         "CFBundleVersion": "com.microsoft.onedrive",
    #         "application_name": "OneDrive.app",
    #         "min_os": "N/A",
    #         "last_updated": "N/A",
    #         "application_id": "OneDrive.app"
    #     },
    #     "keys": {
    #         "full_update_download": "PkgBinaryURL",
    #         "short_version": "CFBundleShortVersionString",
    #         "full_version": "CFBundleVersion",
    #         "app_only_update_download": "PkgBinaryURL"
    #     }
    # },
    "Skype": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSFB16.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.skypeforbusiness",
            "application_name": "Skype for Business.app",
            # Skype for Business is EOL. Its MAU manifest is frozen at 16.31.11 (Sep 2024)
            # and ships only an updater pkg, so pin to the newer standalone full installer
            # (re-packaged Jan 2026). No live CDN source exists for this full-installer build.
            "full_update_download": "https://download.microsoft.com/download/5ea1d93d-e654-4865-a75a-0d90256e4f25/Skype%20for%20Business%20on%20Mac%20Installer%2016.31.0.31.pkg",
            "app_only_update_download": "https://download.microsoft.com/download/5ea1d93d-e654-4865-a75a-0d90256e4f25/Skype%20for%20Business%20on%20Mac%20Installer%2016.31.0.31.pkg",
            "short_version": "16.31.0.31",
            "full_version": "16.31.0.31",
            "last_updated": "January 20, 2026",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Teams": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409TEAMS21.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.teams",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2249065",
            "application_name": "Microsoft Teams.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },    "Intune": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409IMCP01.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.intune.companyportal",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=853070",
            "application_name": "Company Portal.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS Version"
        }
    },
    # "Edge": { ######## MOVED OVER TO ITS OWN FILE MACOS_STANDALONE_EDGE_LATEST.* ########
    #     "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409EDGE01.xml",
    #     "manual_entries": {
    #         "CFBundleVersion": "com.microsoft.edgemac",
    #         "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2093504",
    #         "application_name": "Microsoft Edge.app",
    #     },
    #     "keys": {
    #         "application_id": "Application ID",
    #         "short_version": "Title",
    #         "full_version": "Update Version",
    #         "app_only_update_download": "Location",
    #         "last_updated": "Date",
    #         "min_os": "Minimum OS"
    #     }
    # },
    "Defender For Endpoint": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409WDAV00.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2097502",
            "application_name": "Microsoft Defender.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Defender for Consumers": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409WDAVCONSUMER.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2247001",
            "application_name": "Microsoft Defender.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Defender Shim": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409WDAVSHIM.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "application_name": "N/A",
        },
        "keys": {
            "application_id": "Application ID",
            "full_update_download": "Location",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Windows App": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSRD10.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.windows.app",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=868963",
            "application_name": "Windows App.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS Version"
        }
    },
    "Visual": {
        "url": "https://update.code.visualstudio.com/api/update/darwin-universal/stable/384ff7382de624fb94dbaf6da11977bba1ecd427",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.visualstudio",
            "full_update_download": "https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal-dmg",
            "application_name": "Visual Studio Code.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "name",
            "full_version": "productVersion",
            "app_only_update_download": "url",
            "last_updated": "timestamp",
            "min_os": "Minimum OS"
        }
    },
    "Copilot": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSCP10.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.m365copilot",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2325438",
            "application_name": "Microsoft 365 Copilot.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "MAU": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSau04.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.autoupdate",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=830196",
            "application_name": "Microsoft AutoUpdate.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Licensing Helper Tool": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409OLIC02.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.office.licensingV2.helper",
            "application_name": "N/A",
        },
        "keys": {
            "full_update_download": "Location",
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Quick Assist": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSQA01.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.quickassist",
        },
        "keys": {
            "full_update_download": "Location",
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Update Version",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    },
    "Remote Help": {
        "url": "https://officecdnmac.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/0409MSRH01.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.remotehelp"
        },
        "keys": {
            "full_update_download": "Location",
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Update Version",
            "full_version": "Update Version",
            "app_only_update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS"
        }
    }
}

# Capture the current last update date and time
last_update_date_time = get_current_date_time()

# Initialize root element for combined XML
root = ET.Element("latest")

# Add the last update date and time element to the XML
last_update_element = ET.SubElement(root, "last_updated")
last_update_element.text = last_update_date_time  # Value from get_current_date_time()

# Skip SHA1/SHA256 downloads for testing. Default False (production); set env
# MOFA_SKIP_SHA=true for a fast local run that avoids downloading every package.
skip_sha_checks = os.environ.get("MOFA_SKIP_SHA", "false").lower() in ("1", "true", "yes")

# --- CDN host handling -------------------------------------------------------
# MAU itself reads collateral from the OneCDN host; "officecdnmac" is a legacy
# mirror that lags every ring (it was reporting 16.109 while the live ring served
# 16.110). Prefer OneCDN and fall back to the legacy host only if OneCDN fails.
LEGACY_CDN = "officecdnmac.microsoft.com/pr/"
ONECDN = "res.public.onecdn.static.microsoft/mro1cdnstorage/"
REQUEST_TIMEOUT = (10, 120)  # (connect, read) seconds — never hang the Action

def to_onecdn(url):
    """Rewrite a legacy officecdnmac collateral URL to the live OneCDN host."""
    return url.replace(LEGACY_CDN, ONECDN)

def chk_url(url):
    """Derive the lightweight -chk.xml pointer URL from a base 0409<App>.xml URL."""
    if url.endswith(".xml") and "-chk.xml" not in url:
        return url[:-4] + "-chk.xml"
    return None

def version_tuple(v):
    """Parse a version string into a comparable tuple of ints.

    Non-numeric/empty values sort lowest. MAU '99999' sentinels (used for
    special-cased titles like Windows App / Intune whose real version lives in
    the manifest Title) are treated as no-version so they never win a max().
    """
    if not v or not isinstance(v, str):
        return ()
    parts = re.findall(r"\d+", v)
    if not parts:
        return ()
    t = tuple(int(p) for p in parts)
    return () if t == (99999,) else t

def fetch_xml(url):
    """GET a collateral file from OneCDN first, then the legacy host.

    Returns the requests.Response or None if every host failed.
    """
    candidates = [to_onecdn(url)]
    if candidates[0] != url:
        candidates.append(url)  # legacy fallback
    for u in candidates:
        try:
            r = requests.get(u, allow_redirects=True, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as e:
            logging.warning(f"Fetch failed ({u}): {e}")
    return None

# Function to read existing XML data from macos_standalone_latest.xml
def read_existing_xml(filename):
    if not os.path.exists(filename):
        logging.warning(f"File {filename} does not exist.")
        return {}

    try:
        logging.info(f"Reading existing XML data from {filename}...")
        tree = ET.parse(filename)
        root = tree.getroot()
        existing_data = {}
        for package in root.findall("package"):
            app_name = package.find("name").text
            last_updated = package.find("last_updated").text
            existing_data[app_name] = {
                "last_updated": last_updated,
                "data": {child.tag: child.text for child in package}
            }
        logging.info(f"Successfully read existing XML data from {filename}.")
        return existing_data
    except ET.ParseError as e:
        logging.error(f"XML parsing error in {filename}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error reading existing XML from {filename}: {e}")
        return {}

# Read existing data from macos_standalone_latest.xml
existing_data = read_existing_xml("latest_raw_files/macos_standalone_latest.xml")

# Function to fetch and process an app's data (either XML or JSON)
def fetch_and_process(app_name, config):
    try:
        logging.info("-" * 50)
        logging.info(f"Fetching data for {app_name} from {config['url']}...")
        response = fetch_xml(config["url"])
        if response is None:
            raise RuntimeError(f"all CDN hosts failed for {config['url']}")

        logging.info(f"Response status code: {response.status_code}")

        # Check if the response is in JSON format
        if response.headers.get('Content-Type', '').startswith('application/json'):
            app_data = response.json()
            logging.info(f"JSON data: {app_data}")
            extracted_data = process_json_data(app_data, config)
        else:
            # Poll the base manifest a few times and keep the parse with the HIGHEST
            # Update Version. OneCDN edges briefly serve a stale version during a wave;
            # picking the best *whole* response (instead of patching a single field)
            # keeps every field — short_version, full_version, date, download URLs —
            # internally consistent for the same build.
            best, best_v = None, ()
            for attempt in range(3):
                resp = response if attempt == 0 else fetch_xml(config["url"])
                if resp is None:
                    continue
                try:
                    app_data = ET.fromstring(resp.content).find(".//dict")
                except Exception as e:
                    logging.warning(f"{app_name}: manifest parse failed: {e}")
                    continue
                cand = process_xml_data(app_data, config)
                cv = version_tuple(cand.get("full_version", ""))
                if best is None or cv > best_v:
                    best, best_v = cand, cv
            if best is None:
                raise RuntimeError(f"no parseable manifest for {config['url']}")
            extracted_data = best

        # Add manual entries
        extracted_data.update(config["manual_entries"])

        # Special handling for Copilot short_version: remove leading "365"
        if app_name == "Copilot":
            sv = extracted_data.get("short_version", "")
            if isinstance(sv, str):
                extracted_data["short_version"] = re.sub(r'^\s*365[\s\-–—]*', '', sv).strip()

        logging.info(f"Extracted data: {extracted_data}")

        # Special handling for OneDrive
        if app_name == "OneDrive":
            extracted_data["last_updated"] = last_update_date_time  # Use current date and time as last_updated

        # Recompute hashes only when something changed; otherwise reuse existing data.
        if app_name in existing_data:
            existing_app_data = existing_data[app_name]["data"]
            # Guard against transient OneCDN edge-cache flux: never downgrade a
            # published version. A lower fetched version almost always means a stale
            # edge node, not a real rollback (observed: Word flipping 16.110 -> 16.109).
            # Skip this for hardcoded versions (manual_entries) — e.g. Skype's
            # 16.31.0.31 must win over an older-looking published 16.31.31.
            if "full_version" not in config.get("manual_entries", {}) and \
                    version_tuple(existing_app_data.get("full_version", "")) > version_tuple(extracted_data.get("full_version", "")):
                logging.warning(
                    f"{app_name}: fetched {extracted_data.get('full_version')} < published "
                    f"{existing_app_data.get('full_version')}; keeping published (likely CDN flux)")
                add_to_combined_xml(app_name, existing_app_data)
                return
            changes_detected = any(
                extracted_data[key] != existing_app_data.get(key, "N/A")
                for key in extracted_data
            )
            if not changes_detected:
                if has_missing_hashes(existing_app_data, extracted_data):
                    logging.info(f"{app_name}: version unchanged but hash(es) N/A; retrying those downloads.")
                    add_to_combined_xml(app_name, refill_missing_hashes(existing_app_data, extracted_data))
                else:
                    logging.info(f"No update for {app_name}. Skipping SHA checks.")
                    add_to_combined_xml(app_name, existing_app_data)
                return
            logging.info(f"Update detected for {app_name}.")
        else:
            logging.info(f"New app {app_name} detected.")

        assign_hashes(extracted_data)
        add_to_combined_xml(app_name, extracted_data)

    except Exception as e:
        logging.error(f"Error processing {app_name}: {e}")
        # Use existing data if processing fails
        if app_name in existing_data:
            logging.info(f"Reverting to existing data for {app_name}.")
            add_to_combined_xml(app_name, existing_data[app_name]["data"])

# Function to process XML data
def process_xml_data(app_data, config):
    logging.info("Processing XML data...")
    extracted_data = {}
    for field, key in config["keys"].items():
        extracted_data[field] = find_key_value(app_data, key)

    last_updated = extracted_data.get("last_updated", "N/A")
    extracted_data["last_updated"] = convert_last_updated(last_updated)

    if 'short_version' in extracted_data:
        extracted_data["short_version"] = re.sub(r'[a-zA-Z]', '', extracted_data["short_version"]).lstrip()

    logging.info("Successfully processed XML data.")
    return extracted_data

# Helper function to find a key's value in the XML
def find_key_value(element, key_name):
    if element.tag == "dict":
        found = False
        for child in element:
            if found:
                logging.info(f"Found value for key {key_name}: {child.text}")
                return child.text if child.text else "N/A"
            if child.tag == "key" and child.text == key_name:
                found = True
    elif element.tag == "array":
        for item in element:
            value = find_key_value(item, key_name)
            if value != "N/A":
                return value
    # Recursively search nested dicts and arrays
    for child in element:
        if child.tag in ["dict", "array"]:
            value = find_key_value(child, key_name)
            if value != "N/A":
                return value
    return "N/A"

# Function to process JSON data
def process_json_data(app_data, config):
    extracted_data = {}
    for field, key in config["keys"].items():
        extracted_data[field] = app_data.get(key, "N/A")

    last_updated = extracted_data.get("last_updated", "N/A")
    extracted_data["last_updated"] = convert_last_updated(last_updated)

    if 'short_version' in extracted_data:
        extracted_data["short_version"] = re.sub(r'[a-zA-Z]', '', extracted_data["short_version"]).lstrip()

    return extracted_data

# Cache hashes per URL so a package shared by full + app-only links is downloaded once.
_hash_cache = {}

# Download a package once and compute both SHA1 and SHA256 in a single streaming pass.
def compute_hashes(url):
    if not url:
        return "N/A", "N/A"
    if url in _hash_cache:
        return _hash_cache[url]
    try:
        logging.info(f"Hashing {url}...")
        h1, h256 = sha1(), sha256()
        with requests.get(url, stream=True, allow_redirects=True, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=1 << 20):  # 1 MiB
                h1.update(chunk)
                h256.update(chunk)
        result = (h1.hexdigest(), h256.hexdigest())
        logging.info(f"SHA1 {result[0]} / SHA256 {result[1]} for {url}")
    except Exception as e:
        logging.error(f"Error hashing {url}: {e}")
        result = ("N/A", "N/A")
    _hash_cache[url] = result
    return result

# Pairs of (download-URL field, its SHA1 field, its SHA256 field).
_HASH_FIELDS = [
    ("full_update_download", "full_update_sha1", "full_update_sha256"),
    ("app_only_update_download", "app_update_sha1", "app_update_sha256"),
]

# Populate the four hash fields for an app from its full + app-only download URLs.
def assign_hashes(data):
    if skip_sha_checks:
        for _u, s1, s256 in _HASH_FIELDS:
            data[s1] = data[s256] = "N/A"
        return
    for url_key, s1, s256 in _HASH_FIELDS:
        data[s1], data[s256] = compute_hashes(data.get(url_key))

def has_missing_hashes(existing, data):
    """True if a SHA is N/A but its download URL is a real http link, so it
    should be hashable. Lets us retry a previously-failed hash even when the
    version is unchanged (a transient download failure leaves a sticky N/A)."""
    for url_key, _s1, s256 in _HASH_FIELDS:
        url = data.get(url_key) or existing.get(url_key)
        if url and str(url).startswith("http") and existing.get(s256, "N/A") in ("N/A", None, ""):
            return True
    return False

def refill_missing_hashes(existing, data):
    """Copy of existing with only the N/A-but-hashable SHAs recomputed; good
    hashes are preserved and a retry that fails again is left as N/A."""
    out = dict(existing)
    for url_key, s1, s256 in _HASH_FIELDS:
        url = data.get(url_key) or existing.get(url_key)
        if url and str(url).startswith("http") and existing.get(s256, "N/A") in ("N/A", None, ""):
            h1, h256 = compute_hashes(url)
            if h1 != "N/A":
                out[s1], out[s256] = h1, h256
    return out

def add_to_combined_xml(app_name, data):
    logging.info(f"Adding {app_name} to combined XML...")
    package = ET.SubElement(root, "package")

    # Add the elements in the specified order
    order = [
        "name",
        "application_id",
        "application_name",
        "CFBundleVersion",
        "short_version",
        "full_version",
        "last_updated",
        "min_os",
        "app_only_update_download",
        "app_update_sha1",
        "app_update_sha256",
        "full_update_download",
        "full_update_sha1",
        "full_update_sha256"
    ]

    for key in order:
        if key == "name":  # Ensure the name element is added only once
            name_element = ET.SubElement(package, key)
            name_element.text = app_name
        elif key in data:
            ET.SubElement(package, key).text = data[key]

    logging.info(f"Successfully added {app_name} to combined XML.")

# Function to convert last_updated to human-readable date
def convert_last_updated(last_updated):
    if isinstance(last_updated, int) or (last_updated.isdigit() if isinstance(last_updated, str) else False):
        return time.strftime('%B %d, %Y', time.gmtime(int(last_updated) / 1000))
    elif isinstance(last_updated, str):
        try:
            date_obj = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            return date_obj.strftime('%B %d, %Y')
        except ValueError:
            pass
    return "N/A"

# Process each app and populate combined XML
for app_name, config in apps.items():
    fetch_and_process(app_name, config)

# Pretty print the XML
def pretty_print_xml(element):
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

# Save the updated XML
output_file = "latest_raw_files/macos_standalone_latest.xml"
pretty_xml = pretty_print_xml(root)

# Ensure the directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(pretty_xml)

logging.info("-" * 50)
logging.info(f"XML output generated at: {output_file}")

# Generate and save YAML output in the same order as XML
yaml_data = {
    "last_updated": last_update_date_time,
    "packages": []
}

# Define the order of fields to match the XML
field_order = [
    "name",
    "application_id",
    "application_name",
    "CFBundleVersion",
    "short_version",
    "full_version",
    "last_updated",
    "min_os",
    "app_only_update_download",
    "app_update_sha1",
    "app_update_sha256",
    "full_update_download",
    "full_update_sha1",
    "full_update_sha256"
]

# Read the XML file
xml_file = "latest_raw_files/macos_standalone_latest.xml"
if os.path.exists(xml_file):
    tree = ET.parse(xml_file)
    xml_root = tree.getroot()

    # Extract packages from XML
    for package in xml_root.findall("package"):
        package_data = {"name": package.find("name").text}
        for field in field_order:
            if field != "name":
                element = package.find(field)
                package_data[field] = element.text if element is not None else "N/A"
        yaml_data["packages"].append(package_data)

# Save the YAML file
yaml_output_file = "latest_raw_files/macos_standalone_latest.yaml"

# Ensure the directory exists
os.makedirs(os.path.dirname(yaml_output_file), exist_ok=True)

# Delete existing YAML file if it exists
if os.path.exists(yaml_output_file):
    os.remove(yaml_output_file)

# Write the YAML data to the file
with open(yaml_output_file, "w", encoding="utf-8") as yaml_file:
    yaml.dump(yaml_data, yaml_file, default_flow_style=False, sort_keys=False)

logging.info(f"YAML output generated at: {yaml_output_file}")

# Generate and save JSON output in the same order as XML
json_output_file = "latest_raw_files/macos_standalone_latest.json"

# Ensure the directory exists
os.makedirs(os.path.dirname(json_output_file), exist_ok=True)

# Delete existing JSON file if it exists
if os.path.exists(json_output_file):
    os.remove(json_output_file)

# Write the JSON data to the file
with open(json_output_file, "w", encoding="utf-8") as json_file:
    json.dump(yaml_data, json_file, indent=4)

logging.info(f"JSON output generated at: {json_output_file}")
