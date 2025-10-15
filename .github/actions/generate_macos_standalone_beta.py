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
    "Word": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409MSWD2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.word",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "FullUpdaterLocation"
        }
    },
    "Excel": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409XCEL2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.excel",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "FullUpdaterLocation"
        }
    },
    "PowerPoint": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409PPT32019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.powerpoint",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "FullUpdaterLocation"
        }
    },
    "Outlook": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409OPIM2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.outlook",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "FullUpdaterLocation"
        }
    },
    "OneNote": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409ONMC2019.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.onenote",
        },
        "keys": {
            "application_id": "Application ID",
            "application_name": "Application Name",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "FullUpdaterLocation",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "FullUpdaterLocation"
        }
    },
    # "OneDrive": { ######## MOVED OVER TO ITS OWN FILE MACOS_STANDALONE_ONEDRIVE_LATEST.* ########
    #     "url": "https://g.live.com/0USSDMC_W5T/MacODSUInsiders",
    #     "manual_entries": {
    #         "CFBundleVersion": "com.microsoft.onedrive",
    #         "application_name": "OneDrive.app",
    #         "min_os": "N/A",
    #         "last_updated": "N/A",
    #         "application_id": "OneDrive.app"
    #     },
    #     "keys": {
    #         "latest_download": "PkgBinaryURL",
    #         "short_version": "CFBundleShortVersionString",
    #         "full_version": "CFBundleVersion",
    #         "update_download": "PkgBinaryURL"
    #     }
    # },
    "Skype": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409MSFB16.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.skypeforbusiness",
            "application_name": "Skype for Business.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Teams": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409TEAMS21.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.teams",
            "application_name": "Microsoft Teams.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },    "Intune": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409IMCP01.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.intune.companyportal",
            "application_name": "Company Portal.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS Version",
            "latest_download": "Location"
        }
    },
    "Edge": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409EDGE01.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.edgemac",
            "application_name": "Microsoft Edge.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Defender For Endpoint": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409WDAV00.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "application_name": "Microsoft Defender.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Defender For Consumers": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409WDAVCONSUMER.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "application_name": "Microsoft Defender.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Defender Shim": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409WDAVSHIM.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.defender.endpoint",
            "application_name": "Microsoft Defender.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Visual": {
        "url": "https://update.code.visualstudio.com/api/update/darwin-universal/insider/92d25e35d9bf1a6b16f7d0758f25d48ace11e5b9",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.VSCodeInsiders",
            "latest_download": "https://code.visualstudio.com/sha/download?build=insider&os=darwin-universal",
            "application_name": "Visual Studio Code - Insiders.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "name",
            "full_version": "productVersion",
            "update_download": "url",
            "last_updated": "timestamp",
            "min_os": "Minimum OS"
        }
    },
    "Copilot": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409MSCP10.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.m365copilot",
            "application_name": "Microsoft 365 Copilot.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "MAU": {
        "url": "https://officecdnmac.microsoft.com/pr/4B2D7701-0A4F-49C8-B4CB-0C2D4043F51F/MacAutoupdate/0409MSau04.xml",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.autoupdate",
            "application_name": "Microsoft AutoUpdate.app",
        },
        "keys": {
            "application_id": "Application ID",
            "short_version": "Title",
            "full_version": "Update Version",
            "update_download": "Location",
            "last_updated": "Date",
            "min_os": "Minimum OS",
            "latest_download": "Location"
        }
    },
    "Windows App Beta": {
        "type": "appcenter",
        "base": "https://install.appcenter.ms/api/v0.1/apps/rdmacios-k2vy/microsoft-remote-desktop-for-mac/distribution_groups/all-users-of-microsoft-remote-desktop-for-mac",
        "manual_entries": {
            "CFBundleVersion": "com.microsoft.windows.app",
            "application_name": "Windows App Beta.app",
            "application_id": "N/A",
            "min_os": "N/A"
        },
        "keys": {
            "short_version": "short_version",
            "full_version": "short_version",
            "last_updated": "uploaded_at",
            "update_download": "download_url",
            "latest_download": "download_url"
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
existing_data = read_existing_xml("latest_raw_files/macos_standalone_beta.xml")

# Function to fetch and process an app's data (either XML or JSON)
def fetch_and_process(app_name, config):
    try:
        logging.info("-" * 50)
        # App Center special handling (two-step JSON: list then details)
        if config.get("type") == "appcenter":
            base = config.get("base")
            if not base:
                raise ValueError(f"Missing 'base' for App Center app: {app_name}")

            list_url = f"{base}/public_releases"
            logging.info(f"Fetching App Center releases for {app_name} from {list_url}...")
            list_resp = requests.get(list_url, timeout=30)
            list_resp.raise_for_status()
            releases = list_resp.json()

            if not releases:
                raise ValueError(f"No App Center releases found for {app_name} (group may be private).")

            latest = releases[0]
            release_id = latest.get("id")
            if not release_id:
                raise ValueError(f"Latest App Center release missing 'id' for {app_name}.")

            detail_url = f"{base}/releases/{release_id}"
            logging.info(f"Fetching App Center release details for {app_name} from {detail_url}...")
            detail_resp = requests.get(detail_url, timeout=30)
            detail_resp.raise_for_status()
            info = detail_resp.json()

            extracted_data = process_json_data(info, config)
            extracted_data.update(config.get("manual_entries", {}))
            # Special handling for Copilot short_version: remove leading "365"
            if app_name == "Copilot":
                sv = extracted_data.get("short_version", "")
                if isinstance(sv, str):
                    extracted_data["short_version"] = re.sub(r'^\s*365[\s\-–—]*', '', sv).strip()
            logging.info(f"Extracted data (App Center): {extracted_data}")

            # Special handling for OneDrive
            if app_name == "OneDrive":
                extracted_data["last_updated"] = last_update_date_time

            # Change detection and SHA handling
            if app_name in existing_data:
                existing_app_data = existing_data[app_name]["data"]
                # Only compare short_version for App Center updates
                old_short = existing_app_data.get("short_version", "N/A")
                new_short = extracted_data.get("short_version", "N/A")
                changes_detected = old_short != new_short
                logging.info(f"App Center change check (short_version): old={old_short}, new={new_short}, changed={changes_detected}")

                if not changes_detected:
                    logging.info(f"No update for {app_name}. Skipping SHA checks.")
                    add_to_combined_xml(app_name, existing_app_data)
                else:
                    logging.info(f"Update detected for {app_name}.")
                    download_url = extracted_data.get("latest_download")
                    if extracted_data.get("sha1", "N/A") == "N/A":
                        logging.info(f"Download URL for SHA1: {download_url}")
                        extracted_data["sha1"] = compute_sha1(download_url) if download_url else "N/A"
                    if extracted_data.get("sha256", "N/A") == "N/A":
                        logging.info(f"Download URL for SHA256: {download_url}")
                        extracted_data["sha256"] = compute_sha256(download_url) if download_url else "N/A"
                    add_to_combined_xml(app_name, extracted_data)
            else:
                logging.info(f"New app {app_name} detected.")
                download_url = extracted_data.get("latest_download")
                logging.info(f"Download URL for SHA1: {download_url}")
                extracted_data["sha1"] = compute_sha1(download_url) if download_url else "N/A"
                logging.info(f"Download URL for SHA256: {download_url}")
                extracted_data["sha256"] = compute_sha256(download_url) if download_url else "N/A"
                add_to_combined_xml(app_name, extracted_data)

            return  # Important: stop here for App Center path

        logging.info(f"Fetching data for {app_name} from {config['url']}...")
        response = requests.get(config["url"], allow_redirects=True)
        response.raise_for_status()

        logging.info(f"Response status code: {response.status_code}")
        # logging.info(f"Response headers: {response.headers}") # Uncomment to view response headers

        # Check if the response is in JSON format
        if response.headers['Content-Type'].startswith('application/json'):
            app_data = response.json()
            logging.info(f"JSON data: {app_data}")
            extracted_data = process_json_data(app_data, config)
        else:
            app_root = ET.fromstring(response.content)
            app_data = app_root.find(".//dict")
            # logging.info(f"XML data: {ET.tostring(app_root, encoding='utf8').decode('utf8')}") # Uncomment to view XML data
            extracted_data = process_xml_data(app_data, config)

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

        # Check if any field has changed or if sha1 or sha256 are "N/A"
        if app_name in existing_data:
            existing_app_data = existing_data[app_name]["data"]
            changes_detected = False
            for key in extracted_data:
                if extracted_data[key] != existing_app_data.get(key, "N/A"):
                    changes_detected = True
                    break

            if not changes_detected:
                logging.info(f"No update for {app_name}. Skipping SHA checks.")
                add_to_combined_xml(app_name, existing_app_data)
            else:
                logging.info(f"Update detected for {app_name}.")
                # Use existing SHA values if they are present and not "N/A"
                if extracted_data.get("sha1", "N/A") == "N/A":
                    download_url = extracted_data.get("latest_download")
                    logging.info(f"Download URL for SHA1: {download_url}")
                    extracted_data["sha1"] = compute_sha1(download_url) if download_url else "N/A"
                if extracted_data.get("sha256", "N/A") == "N/A":
                    download_url = extracted_data.get("latest_download")
                    logging.info(f"Download URL for SHA256: {download_url}")
                    extracted_data["sha256"] = compute_sha256(download_url) if download_url else "N/A"
                add_to_combined_xml(app_name, extracted_data)
        else:
            logging.info(f"New app {app_name} detected.")
            download_url = extracted_data.get("latest_download")
            logging.info(f"Download URL for SHA1: {download_url}")
            extracted_data["sha1"] = compute_sha1(download_url) if download_url else "N/A"
            logging.info(f"Download URL for SHA256: {download_url}")
            extracted_data["sha256"] = compute_sha256(download_url) if download_url else "N/A"
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

# Function to compute SHA1 hash
def compute_sha1(url):
    try:
        logging.info(f"Computing SHA1 for {url}...")
        # Use allow_redirects=True to follow redirects
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()  # Raise exception for HTTP errors
        hasher = sha1()
        for chunk in response.iter_content(chunk_size=8192):
            hasher.update(chunk)
        sha1_hash = hasher.hexdigest()
        logging.info(f"SHA1 for {url}: {sha1_hash}")
        return sha1_hash
    except Exception as e:
        logging.error(f"Error computing SHA1 for {url}: {e}")
        return "N/A"

# Function to compute SHA256 hash
def compute_sha256(url):
    try:
        logging.info(f"Computing SHA256 for {url}...")
        # Use allow_redirects=True to follow redirects
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()  # Raise exception for HTTP errors
        hasher = sha256()
        for chunk in response.iter_content(chunk_size=8192):
            hasher.update(chunk)
        sha256_hash = hasher.hexdigest()
        logging.info(f"SHA256 for {url}: {sha256_hash}")
        return sha256_hash
    except Exception as e:
        logging.error(f"Error computing SHA256 for {url}: {e}")
        return "N/A"

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
        "update_download",
        "latest_download",
        "sha1",
        "sha256",
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
output_file = "latest_raw_files/macos_standalone_beta.xml"
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
    "update_download",
    "latest_download",
    "sha1",
    "sha256",
]

# Read the XML file
xml_file = "latest_raw_files/macos_standalone_beta.xml"
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
yaml_output_file = "latest_raw_files/macos_standalone_beta.yaml"

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
json_output_file = "latest_raw_files/macos_standalone_beta.json"

# Ensure the directory exists
os.makedirs(os.path.dirname(json_output_file), exist_ok=True)

# Delete existing JSON file if it exists
if os.path.exists(json_output_file):
    os.remove(json_output_file)

# Write the JSON data to the file
with open(json_output_file, "w", encoding="utf-8") as json_file:
    json.dump(yaml_data, json_file, indent=4)

logging.info(f"JSON output generated at: {json_output_file}")
