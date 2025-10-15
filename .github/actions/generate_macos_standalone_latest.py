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
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=832978",
            "application_name": "Skype for Business.app",
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
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=2156837",
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
            "full_update_download": "Location",
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
            "full_update_download": "Location",
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

# Variable to skip SHA1 and SHA256 checks for testing purposes (set to False for production)
skip_sha_checks = False

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
                # Ensure SHA values are computed for both URLs
                if skip_sha_checks:
                    extracted_data["full_update_sha1"] = "N/A"
                    extracted_data["full_update_sha256"] = "N/A"
                    extracted_data["app_update_sha1"] = "N/A"
                    extracted_data["app_update_sha256"] = "N/A"
                else:
                    full_download_url = extracted_data.get("full_update_download")
                    app_download_url = extracted_data.get("app_only_update_download")
                    
                    # Compute hashes for full update download
                    extracted_data["full_update_sha1"] = compute_sha1(full_download_url) if full_download_url else "N/A"
                    extracted_data["full_update_sha256"] = compute_sha256(full_download_url) if full_download_url else "N/A"
                    
                    # Compute hashes for app-only update download
                    extracted_data["app_update_sha1"] = compute_sha1(app_download_url) if app_download_url else "N/A"
                    extracted_data["app_update_sha256"] = compute_sha256(app_download_url) if app_download_url else "N/A"
                
                add_to_combined_xml(app_name, extracted_data)
        else:
            logging.info(f"New app {app_name} detected.")
            # Ensure SHA values are computed for both URLs
            if skip_sha_checks:
                extracted_data["full_update_sha1"] = "N/A"
                extracted_data["full_update_sha256"] = "N/A"
                extracted_data["app_update_sha1"] = "N/A"
                extracted_data["app_update_sha256"] = "N/A"
            else:
                full_download_url = extracted_data.get("full_update_download")
                app_download_url = extracted_data.get("app_only_update_download")
                
                # Compute hashes for full update download
                extracted_data["full_update_sha1"] = compute_sha1(full_download_url) if full_download_url else "N/A"
                extracted_data["full_update_sha256"] = compute_sha256(full_download_url) if full_download_url else "N/A"
                
                # Compute hashes for app-only update download
                extracted_data["app_update_sha1"] = compute_sha1(app_download_url) if app_download_url else "N/A"
                extracted_data["app_update_sha256"] = compute_sha256(app_download_url) if app_download_url else "N/A"
            
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
