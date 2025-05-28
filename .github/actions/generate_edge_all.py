import os
import requests
import plistlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import re
import json
import yaml
from collections import defaultdict
import pytz
import hashlib

# Define the Eastern Time Zone
eastern = pytz.timezone('US/Eastern')

def fetch_edge_latest(channel, url):
    response = requests.get(url)
    response.raise_for_status()
    
    xml_content = response.text
    
    output_dir = "latest_edge_files"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory '{output_dir}' created or already exists.")
    
    output_file = os.path.join(output_dir, f"edge_{channel}_version.xml")
    with open(output_file, "w") as file:
        file.write(xml_content)
    print(f"File '{output_file}' written successfully.")
    return output_file

def extract_info_from_xml(file_path):
    try:
        with open(file_path, 'rb') as file:
            plist_data = plistlib.load(file)
        
        # Debug prints to check the structure of the plist
        print(f"Parsing plist file: {file_path}")
        print(plist_data)
        
        date = plist_data[0].get('Date', 'N/A')
        location = plist_data[0].get('Location', 'N/A')
        title = plist_data[0].get('Title', 'N/A')
        
        # Format the title to only include numbers and special characters
        version = re.sub(r'[^0-9.]+', '', title)
        
        # Format the date to a user-readable format
        if date != 'N/A':
            date = date.astimezone(eastern).strftime('%B %d, %Y %I:%M %p %Z')
        
        return {
            "channel": os.path.basename(file_path).split('_')[1],
            "date": date,
            "location": location,
            "version": version
        }
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return {
            "channel": os.path.basename(file_path).split('_')[1],
            "date": 'N/A',
            "location": 'N/A',
            "version": 'N/A'
        }

def create_summary_xml(info_list, insider_info_list, output_file):
    root = ET.Element("EdgeLatestVersions")
    
    # Add last_updated element
    last_updated = ET.SubElement(root, "last_updated")
    last_updated.text = datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z')
    
    for info in info_list:
        entry = ET.SubElement(root, "Version")
        ET.SubElement(entry, "Channel").text = info["channel"]
        ET.SubElement(entry, "Date").text = info["date"]
        ET.SubElement(entry, "Location").text = info["location"]
        ET.SubElement(entry, "Version").text = info["version"]
    
    for info in insider_info_list:
        entry = ET.SubElement(root, "Version")
        ET.SubElement(entry, "Channel").text = f"insider_{info['channel']}"
        ET.SubElement(entry, "Date").text = info["date"]
        ET.SubElement(entry, "Location").text = info["location"]
        ET.SubElement(entry, "Version").text = info["version"]
    
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_file, "w") as file:
        file.write(pretty_xml_str)
    print(f"Summary file '{output_file}' written successfully.")

def update_last_updated_in_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Find or create last_updated element
    last_updated = root.find("last_updated")
    if last_updated is None:
        last_updated = ET.Element("last_updated")
        root.insert(0, last_updated)
    
    last_updated.text = datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z')
    
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    # Remove extra newlines and spaces
    pretty_xml_str = "\n".join([line for line in pretty_xml_str.split("\n") if line.strip()])
    
    with open(file_path, "w") as file:
        file.write(pretty_xml_str)
    print(f"Updated file '{file_path}' with last_updated.")

def fetch_edge_insider_canary_version(url):
    response = requests.get(url)
    response.raise_for_status()
    
    releases = response.json()
    macos_releases = [release for release in releases[0]["Releases"] if release["Platform"] == "MacOS"]
    
    if not macos_releases:
        print("No MacOS releases found.")
        return None
    
    latest_release = max(macos_releases, key=lambda x: x["PublishedTime"])
    
    artifact = next((artifact for artifact in latest_release["Artifacts"] if artifact["ArtifactName"] == "pkg"), None)
    location = artifact["Location"] if artifact else "N/A"
    
    return {
        "channel": "canary",
        "date": datetime.strptime(latest_release["PublishedTime"], '%Y-%m-%dT%H:%M:%S').astimezone(eastern).strftime('%B %d, %Y %I:%M %p %Z'),
        "location": location,
        "version": latest_release["ProductVersion"]
    }

def create_canary_xml(info, output_file):
    root = ET.Element("EdgeCanaryVersion")
    
    # Add last_updated element
    last_updated = ET.SubElement(root, "last_updated")
    last_updated.text = datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z')
    
    entry = ET.SubElement(root, "Version")
    ET.SubElement(entry, "Channel").text = info["channel"]
    ET.SubElement(entry, "Date").text = info["date"]
    ET.SubElement(entry, "Location").text = info["location"]
    ET.SubElement(entry, "Version").text = info["version"]
    
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_file, "w") as file:
        file.write(pretty_xml_str)
    print(f"Canary file '{output_file}' written successfully.")

def fetch_edge_insider_version(url, channel):
    response = requests.get(url)
    response.raise_for_status()
    
    releases = response.json()
    macos_releases = [release for release in releases[0]["Releases"] if release["Platform"] == "MacOS"]
    
    if not macos_releases:
        print(f"No MacOS releases found for {channel}.")
        return None
    
    latest_release = max(macos_releases, key=lambda x: x["PublishedTime"])
    
    artifact = next((artifact for artifact in latest_release["Artifacts"] if artifact["ArtifactName"] == "pkg"), None)
    location = artifact["Location"] if artifact else "N/A"
    
    return {
        "channel": channel,
        "date": datetime.strptime(latest_release["PublishedTime"], '%Y-%m-%dT%H:%M:%S').astimezone(eastern).strftime('%B %d, %Y %I:%M %p %Z'),
        "location": location,
        "version": latest_release["ProductVersion"]
    }

def generate_hashes(location_url):
    try:
        response = requests.get(location_url, stream=True)
        response.raise_for_status()
        
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        
        for chunk in response.iter_content(chunk_size=8192):
            sha1.update(chunk)
            sha256.update(chunk)
        
        return sha1.hexdigest(), sha256.hexdigest()
    except Exception as e:
        print(f"Error generating hashes for {location_url}: {e}")
        return "N/A", "N/A"

def should_update_file(local_file, new_date):
    if not os.path.exists(local_file):
        print(f"Local file '{local_file}' does not exist. Proceeding with update.")
        return True
    
    try:
        tree = ET.parse(local_file)
        root = tree.getroot()
        last_updated = root.find("last_updated")
        if last_updated is not None and last_updated.text == new_date:
            print(f"No update needed. Local file '{local_file}' is already up-to-date.")
            return False
        else:
            print(f"Date mismatch detected. Updating file '{local_file}'.")
            return True
    except Exception as e:
        print(f"Error checking local file '{local_file}': {e}. Proceeding with update.")
        return True

def log(message, level="INFO"):
    levels = {
        "INFO": "[INFO]",
        "WARNING": "[WARNING]",
        "ERROR": "[ERROR]",
        "SUCCESS": "[SUCCESS]"
    }
    print(f"{levels.get(level, '[INFO]')} {message}")

def should_update_channel(global_file, channel_name, channel_date):
    log(f"Starting check for channel '{channel_name}' in global file '{global_file}'...")
    if not os.path.isfile(global_file):
        log(f"Global file '{global_file}' does not exist. Proceeding with update for channel '{channel_name}'.", "WARNING")
        return True
    
    try:
        log(f"Parsing global file '{global_file}'...")
        tree = ET.parse(global_file)
        root = tree.getroot()
        
        # Find the specific channel entry
        for version in root.findall("Version"):
            name = version.find("Name")
            last_update = version.find("Last_Update")
            if name is not None and name.text == channel_name:
                log(f"Found channel '{channel_name}' in global file.")
                if last_update is not None and last_update.text == channel_date:
                    log(f"No update needed for channel '{channel_name}'. Global file '{global_file}' is already up-to-date.", "SUCCESS")
                    return False
                else:
                    log(f"Date mismatch detected for channel '{channel_name}'. Updating global file '{global_file}'.", "WARNING")
                    return True
        
        log(f"Channel '{channel_name}' not found in global file '{global_file}'. Proceeding with update.", "WARNING")
        return True
    except ET.ParseError as e:
        log(f"XML parsing error for file '{global_file}': {e}. Proceeding with update.", "ERROR")
        return True
    except Exception as e:
        log(f"Error checking global file '{global_file}' for channel '{channel_name}': {e}. Proceeding with update.", "ERROR")
        return True

def update_global_file(global_file, info_list):
    log(f"Starting update for global file '{global_file}'...")
    if not os.path.isfile(global_file):
        log(f"Global file '{global_file}' does not exist. Creating a new file.", "WARNING")
        create_insider_versions_xml(info_list, global_file)
    else:
        log(f"Parsing global file '{global_file}' for updates...")
        tree = ET.parse(global_file)
        root = tree.getroot()
        
        for info in info_list:
            log(f"Processing channel '{info['channel']}'...")
            updated = False
            for version in root.findall("Version"):
                name = version.find("Name")
                if name is not None and name.text == info["channel"]:
                    log(f"Updating existing entry for channel '{info['channel']}'...")
                    version.find("Version").text = info["version"]
                    version.find("Full_Update_Download").text = info["location"]
                    sha1, sha256 = generate_hashes(info["location"])
                    version.find("Full_Update_Sha1").text = sha1
                    version.find("Full_Update_Sha256").text = sha256
                    version.find("Last_Update").text = info["date"]
                    updated = True
                    log(f"Updated channel '{info['channel']}' in global file.", "SUCCESS")
                    break
            
            if not updated:
                log(f"Adding new entry for channel '{info['channel']}'...")
                entry = ET.SubElement(root, "Version")
                ET.SubElement(entry, "Name").text = info["channel"]
                ET.SubElement(entry, "Version").text = info["version"]
                ET.SubElement(entry, "Application_ID").text = "EDGE01"
                ET.SubElement(entry, "Application_Name").text = "Microsoft Edge.app"
                ET.SubElement(entry, "CFBundleVersion").text = "com.microsoft.edgemac"
                ET.SubElement(entry, "Full_Update_Download").text = info["location"]
                sha1, sha256 = generate_hashes(info["location"])
                ET.SubElement(entry, "Full_Update_Sha1").text = sha1
                ET.SubElement(entry, "Full_Update_Sha256").text = sha256
                ET.SubElement(entry, "Last_Update").text = info["date"]
                log(f"Added new channel '{info['channel']}' to global file.", "SUCCESS")
        
        log(f"Updating last_updated field in global file...")
        last_updated = root.find("last_updated")
        if last_updated is None:
            last_updated = ET.SubElement(root, "last_updated")
        last_updated.text = datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z')
        
        log(f"Writing updates to global file '{global_file}'...")
        tree = ET.ElementTree(root)
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        # Remove unnecessary newlines and spaces
        pretty_xml_str = "\n".join([line for line in pretty_xml_str.split("\n") if line.strip()])
        
        with open(global_file, "w") as file:
            file.write(pretty_xml_str)
        log(f"Global file '{global_file}' updated successfully.", "SUCCESS")
    
    # Generate JSON and YAML outputs
    json_file = global_file.replace(".xml", ".json")
    yaml_file = global_file.replace(".xml", ".yaml")
    log(f"Generating JSON output at '{json_file}'...")
    convert_xml_to_json(global_file, json_file)
    log(f"Generating YAML output at '{yaml_file}'...")
    convert_xml_to_yaml(global_file, yaml_file)

def create_insider_versions_xml(info_list, output_file):
    root = ET.Element("EdgeInsiderVersions")
    
    # Add last_updated element
    last_updated = ET.SubElement(root, "last_updated")
    last_updated.text = datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z')
    
    for info in info_list:
        entry = ET.SubElement(root, "Version")
        ET.SubElement(entry, "Name").text = info["channel"]
        ET.SubElement(entry, "Version").text = info["version"]
        ET.SubElement(entry, "Application_ID").text = "EDGE01"
        ET.SubElement(entry, "Application_Name").text = "Microsoft Edge.app"
        ET.SubElement(entry, "CFBundleVersion").text = "com.microsoft.edgemac"
        ET.SubElement(entry, "Full_Update_Download").text = info["location"]
        
        # Generate hashes for the location URL
        sha1, sha256 = generate_hashes(info["location"])
        ET.SubElement(entry, "Full_Update_Sha1").text = sha1
        ET.SubElement(entry, "Full_Update_Sha256").text = sha256
        
        ET.SubElement(entry, "Last_Update").text = info["date"]
    
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_file, "w") as file:
        file.write(pretty_xml_str)
    print(f"Insider versions file '{output_file}' written successfully.")

def convert_xml_to_json(xml_file, json_file):
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
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d
    
    data_dict = etree_to_dict(root)
    with open(json_file, "w") as file:
        json.dump(data_dict, file, indent=4)
    print(f"JSON file '{json_file}' written successfully.")

def convert_xml_to_yaml(xml_file, yaml_file):
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
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d
    
    data_dict = etree_to_dict(root)
    
    # Create a new dictionary with the desired order
    if "EdgeLatestVersions" in data_dict:
        edge_versions = data_dict["EdgeLatestVersions"]
        ordered_dict = {
            "EdgeLatestVersions": {
                "last_updated": edge_versions.get("last_updated", ""),
                "Version": edge_versions.get("Version", [])
            }
        }
        data_dict = ordered_dict
    
    with open(yaml_file, "w") as file:
        yaml.dump(data_dict, file, default_flow_style=False, sort_keys=False)
    print(f"YAML file '{yaml_file}' written successfully.")

def convert_plist_to_json(xml_file, json_file):
    try:
        with open(xml_file, 'rb') as file:
            plist_data = plistlib.load(file)
        
        # Add last_updated field
        output_data = {
            "last_updated": datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z'),
            "plist_data": plist_data
        }
        
        with open(json_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"JSON file '{json_file}' written successfully.")
    except Exception as e:
        print(f"Error converting plist to JSON: {e}")

def convert_plist_to_yaml(xml_file, yaml_file):
    try:
        with open(xml_file, 'rb') as file:
            plist_data = plistlib.load(file)
        
        # Add last_updated field
        output_data = {
            "last_updated": datetime.now(eastern).strftime('%B %d, %Y %I:%M %p %Z'),
            "plist_data": plist_data
        }
        
        with open(yaml_file, 'w') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"YAML file '{yaml_file}' written successfully.")
    except Exception as e:
        print(f"Error converting plist to YAML: {e}")

if __name__ == "__main__":
    log("Starting Edge version update process...")
    channels = {
        "current": "https://edgeupdates.microsoft.com/api/products/stable",
        "canary": "https://edgeupdates.microsoft.com/api/products/canary",
        "dev": "https://edgeupdates.microsoft.com/api/products/dev",
        "beta": "https://edgeupdates.microsoft.com/api/products/beta"
    }
    
    output_dir = os.path.join(os.getcwd(), "latest_raw_files")
    os.makedirs(output_dir, exist_ok=True)
    global_file = os.path.join(output_dir, "macos_standalone_edge_all.xml")
    
    info_list = []
    for channel, url in channels.items():
        log(f"Fetching data for channel: {channel}")
        info = fetch_edge_insider_version(url, channel)
        if info:
            log(f"Checking if update is needed for channel '{channel}'...")
            if should_update_channel(global_file, channel, info["date"]):
                info_list.append(info)
            else:
                log(f"No updates performed for channel: {channel}", "SUCCESS")
        else:
            log(f"No data fetched for channel: {channel}", "WARNING")
    
    if info_list:
        log("Updating global file with new channel data...")
        update_global_file(global_file, info_list)
    else:
        log("No updates needed for any channel.", "SUCCESS")
    log("Edge version update process completed.")