import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from xml.dom.minidom import parseString
import pytz
import yaml
from collections import defaultdict, OrderedDict
import os

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

# Define common keys
common_keys = {
    "application_name": "trackName",
    "bundleId": "bundleId",
    "version": "version",
    "currentVersionReleaseDate": "currentVersionReleaseDate",
    "releaseNotes": "releaseNotes",
    "minimumOsVersion": "minimumOsVersion",
    "icon_image": "artworkUrl512",
    "app_store_url": "trackViewUrl"
}

# Define app-specific configurations
apps = {
    "MacOS Microsoft Word": {
        "url": "https://itunes.apple.com/search?term=microsoft-word&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Excel": {
        "url": "https://itunes.apple.com/search?term=microsoft-excel&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft PowerPoint": {
        "url": "https://itunes.apple.com/search?term=microsoft-powerpoint&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Outlook": {
        "url": "https://itunes.apple.com/search?term=microsoft-outlook&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft OneNote": {
        "url": "https://itunes.apple.com/search?term=microsoft-onenote&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft OneDrive": {
        "url": "https://itunes.apple.com/search?term=microsoft-onedrive&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS RMS Sharing": {
        "url": "https://itunes.apple.com/search?term=rms-sharing&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Windows App": {
        "url": "https://itunes.apple.com/search?term=windows-app&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft To-Do": {
        "url": "https://itunes.apple.com/search?term=microsoft-to-do&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft CoPilot": {
        "url": "https://itunes.apple.com/search?term=microsoft-copilot&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Azure VPN Client": {
        "url": "https://itunes.apple.com/search?term=azure-vpn-client&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Universal Print": {
        "url": "https://itunes.apple.com/search?term=universal-print&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Rewards for Safari": {
        "url": "https://itunes.apple.com/search?term=microsoft-rewards-for-safari&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Bing for Safari": {
        "url": "https://itunes.apple.com/search?term=microsoft-bing-for-safari&country=us&entity=macSoftware",
        "keys": common_keys
    },
    "MacOS Microsoft Accessory Updater": {
        "url": "https://itunes.apple.com/search?term=microsoft-accessory-updater&country=us&entity=macSoftware",
        "keys": common_keys
    }
}

# Ensure the output directory exists
output_dir = "latest_raw_files"
os.makedirs(output_dir, exist_ok=True)

def fetch_app_data(url):
    logging.info(f"Fetching data from {url}")
    response = requests.get(url)
    data = response.json()
    # logging.info(f"Pulled data: {json.dumps(data, indent=4)}")  # Comment out or remove this line to hide JSON URL output
    return data['results'][0] if 'results' in data and len(data['results']) > 0 else {}

def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return date_obj.strftime('%B %d, %Y')
    except ValueError:
        return date_str

def create_xml(apps):
    root = ET.Element("latest")
    last_updated = ET.SubElement(root, "last_updated")
    last_updated.text = get_current_date_time()

    for app_name, app_info in apps.items():
        logging.info("-" * 50)
        logging.info(f"Processing {app_name}")
        app_data = fetch_app_data(app_info["url"])
        package = ET.SubElement(root, "package")
        ET.SubElement(package, "name").text = app_name
        for key in ["application_name", "bundleId", "currentVersionReleaseDate", "icon_image", "minimumOsVersion", "releaseNotes", "version", "app_store_url"]:
            json_key = app_info["keys"][key]
            value = app_data.get(json_key, "NA")
            if key == "currentVersionReleaseDate" and value != "NA":
                value = format_date(value)
            logging.info(f"{key}: {value}")
            ET.SubElement(package, key).text = value

    # Convert to string and pretty print
    xml_str = ET.tostring(root, encoding='utf-8')
    dom = parseString(xml_str)
    pretty_xml_as_string = dom.toprettyxml()

    with open(os.path.join(output_dir, "macos_appstore_latest.xml"), "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_string)

    logging.info("-" * 50)
    logging.info(f"XML output generated at: {os.path.join(output_dir, 'macos_appstore_latest.xml')}")

def xml_to_json_and_yaml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def etree_to_dict(t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update((k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d

    data_dict = etree_to_dict(root)

    # Reformat the data to match the desired structure
    last_updated = data_dict['latest']['last_updated']
    packages = []
    for package in data_dict['latest']['package']:
        package_data = OrderedDict()
        package_data['name'] = package['name']
        package_data['application_name'] = package['application_name']
        package_data['bundleId'] = package['bundleId']
        package_data['currentVersionReleaseDate'] = package['currentVersionReleaseDate']
        package_data['icon_image'] = package['icon_image']
        package_data['minimumOsVersion'] = package['minimumOsVersion']
        package_data['releaseNotes'] = package['releaseNotes']
        package_data['version'] = package['version']
        package_data['app_store_url'] = package.get('app_store_url', 'NA')
        packages.append(package_data)

    output_data = OrderedDict()
    output_data['last_updated'] = last_updated
    output_data['packages'] = packages

    # Convert to JSON
    with open(os.path.join(output_dir, "macos_appstore_latest.json"), "w", encoding="utf-8") as json_file:
        json.dump(output_data, json_file, indent=4)
    logging.info(f"JSON output generated at: {os.path.join(output_dir, 'macos_appstore_latest.json')}")

    # Convert to YAML using PyYAML with OrderedDict
    class OrderedDumper(yaml.Dumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(OrderedDumper, self).increase_indent(flow, False)

    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    yaml.add_representer(OrderedDict, dict_representer, Dumper=OrderedDumper)

    with open(os.path.join(output_dir, "macos_appstore_latest.yaml"), "w", encoding="utf-8") as yaml_file:
        yaml.dump(output_data, yaml_file, Dumper=OrderedDumper, default_flow_style=False, sort_keys=False)
    logging.info(f"YAML output generated at: {os.path.join(output_dir, 'macos_appstore_latest.yaml')}")

create_xml(apps)
xml_to_json_and_yaml(os.path.join(output_dir, "macos_appstore_latest.xml"))
