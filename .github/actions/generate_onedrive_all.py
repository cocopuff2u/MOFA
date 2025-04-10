import requests
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom.minidom import parseString
import logging
import subprocess
import os
import json
import yaml  # Add this import
from collections import OrderedDict  # Add this import

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_url_content(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def calculate_hash(content, hash_type="sha256"):
    if hash_type == "sha256":
        return hashlib.sha256(content).hexdigest()
    elif hash_type == "sha1":
        return hashlib.sha1(content).hexdigest()
    return None

def extract_from_xml(url, key):
    response = requests.get(url)
    response.raise_for_status()
    tree = ET.fromstring(response.content)
    logging.info(f"Parsing XML from {url} for key '{key}'")
    for parent in tree.iter():
        for element in parent:
            if element.tag == "key" and element.text == key:
                # Look for the next sibling element with the tag "string"
                siblings = list(parent)
                for i, sibling in enumerate(siblings):
                    if sibling == element and i + 1 < len(siblings):
                        next_sibling = siblings[i + 1]
                        if next_sibling.tag == "string":
                            logging.info(f"Found value for key '{key}': {next_sibling.text}")
                            return next_sibling.text
    logging.warning(f"Key '{key}' not found in XML from {url}")
    return None

def fetch_linked_id_version(url):
    try:
        # Corrected the curl command to fetch the version
        result = subprocess.run(
            f"curl -fsIL \"{url}\" | grep -i location: | cut -d '/' -f 6 | cut -d '.' -f 1-3",
            capture_output=True,
            text=True,
            shell=True
        )
        version = result.stdout.strip()
        if version:
            logging.info(f"Fetched version '{version}' for URL: {url}")
            return version
        return "N/A"
    except Exception as e:
        logging.error(f"Error fetching version for URL {url}: {e}")
        return "N/A"

def load_existing_data(file_path):
    """Load existing data from the output XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        existing_data = {}
        for package in root.findall("package"):
            name_element = package.find("name")
            short_version_element = package.find("short_version")
            last_updated_element = package.find("last_updated")
            download_element = package.find("full_update_download")
            sha1_element = package.find("full_update_sha1")
            sha256_element = package.find("full_update_sha256")

            # Ensure elements exist before accessing their text
            name = name_element.text if name_element is not None else None
            short_version = short_version_element.text if short_version_element is not None else None
            last_updated = last_updated_element.text if last_updated_element is not None else None
            download_url = download_element.text if download_element is not None else None
            sha1 = sha1_element.text if sha1_element is not None else "N/A"
            sha256 = sha256_element.text if sha256_element is not None else "N/A"

            if name:
                existing_data[name] = {
                    "short_version": short_version,
                    "last_updated": last_updated,
                    "full_update_download": download_url,
                    "full_update_sha1": sha1,
                    "full_update_sha256": sha256
                }
        return existing_data
    except FileNotFoundError:
        logging.warning(f"{file_path} not found. Starting fresh.")
        return {}
    except Exception as e:
        logging.error(f"Error loading existing data: {e}")
        return {}

def has_version_changed(package_name, new_version, existing_data):
    """Check if the version has changed compared to local data."""
    if package_name not in existing_data:
        logging.info(f"New package detected: '{package_name}'")
        return True
        
    old_version = existing_data[package_name]["short_version"]
    if old_version != new_version:
        logging.info(f"Version change for '{package_name}': {old_version} -> {new_version}")
        return True
        
    logging.info(f"No version change for '{package_name}': still {old_version}")
    return False

def generate_package_xml(package_data, existing_data, now):
    package = ET.Element("package")
    
    package_name = package_data.get("name", "")
    # If we're using existing data (no version change), use all the old data
    if not package_data.get("version_changed", True) and package_name in existing_data:
        existing_package = existing_data[package_name]
        
        # Add elements in the specified order
        name = ET.SubElement(package, "name")
        name.text = package_name

        short_version = ET.SubElement(package, "short_version")
        short_version.text = existing_package["short_version"]

        application_id = ET.SubElement(package, "application_id")
        application_id.text = "ONDR18"

        application_name = ET.SubElement(package, "application_name")
        application_name.text = "OneDrive.app"

        cf_bundle_version = ET.SubElement(package, "CFBundleVersion")
        cf_bundle_version.text = "com.microsoft.onedrive"

        full_update_download = ET.SubElement(package, "full_update_download")
        full_update_download.text = existing_package["full_update_download"]

        full_update_sha1 = ET.SubElement(package, "full_update_sha1")
        full_update_sha1.text = existing_package["full_update_sha1"]

        full_update_sha256 = ET.SubElement(package, "full_update_sha256")
        full_update_sha256.text = existing_package["full_update_sha256"]

        last_updated = ET.SubElement(package, "last_updated")
        last_updated.text = existing_package["last_updated"]  # Keep the original timestamp
    else:
        # Add elements with new data
        name = ET.SubElement(package, "name")
        name.text = package_name

        short_version = ET.SubElement(package, "short_version")
        short_version.text = package_data.get("short_version", "N/A")

        application_id = ET.SubElement(package, "application_id")
        application_id.text = "ONDR18"

        application_name = ET.SubElement(package, "application_name")
        application_name.text = "OneDrive.app"

        cf_bundle_version = ET.SubElement(package, "CFBundleVersion")
        cf_bundle_version.text = "com.microsoft.onedrive"

        full_update_download = ET.SubElement(package, "full_update_download")
        full_update_download.text = package_data.get("full_update_download", "")

        full_update_sha1 = ET.SubElement(package, "full_update_sha1")
        full_update_sha1.text = package_data.get("full_update_sha1", "N/A")

        full_update_sha256 = ET.SubElement(package, "full_update_sha256")
        full_update_sha256.text = package_data.get("full_update_sha256", "N/A")

        last_updated = ET.SubElement(package, "last_updated")
        last_updated.text = now

    return package

def skip_sha_checks():
    # Function to determine if SHA checks should be skipped
    # This can be controlled via an environment variable or a configuration flag
    return False  # Set to True to skip SHA checks

def fetch_package_data(existing_data):
    packages = []

    # URLs with linkid (generate information)
    linkid_urls = [
        {"name": "Deferred Ring", "url": "https://go.microsoft.com/fwlink/?linkid=861009"},
        {"name": "Upcoming Deferred  Ring", "url": "https://go.microsoft.com/fwlink/?linkid=861010"},
        {"name": "Rolling Out (Unknown Use)", "url": "https://go.microsoft.com/fwlink/?linkid=861011"},
        {"name": "App New Version (Unknown Use)", "url": "https://go.microsoft.com/fwlink/?linkid=823060"}
    ]
    for entry in linkid_urls:
        short_version = fetch_linked_id_version(entry["url"])
        version_changed = has_version_changed(entry["name"], short_version, existing_data)
        
        # Only fetch content and calculate hashes if version has changed
        if version_changed and not skip_sha_checks():
            logging.info(f"Fetching content and calculating hashes for {entry['name']}")
            content = fetch_url_content(entry["url"])
            sha1 = calculate_hash(content, "sha1")
            sha256 = calculate_hash(content, "sha256")
        else:
            if entry["name"] in existing_data:
                sha1 = existing_data[entry["name"]]["full_update_sha1"]
                sha256 = existing_data[entry["name"]]["full_update_sha256"]
            else:
                sha1 = "N/A"
                sha256 = "N/A"
            
        package_data = {
            "name": entry["name"],
            "short_version": short_version,
            "full_update_download": entry["url"],
            "full_update_sha1": sha1,
            "full_update_sha256": sha256,
            "version_changed": version_changed
        }
        packages.append(package_data)

    # URLs without linkid (pull XML information)
    xml_urls = [
        {
            "name": "Insider Ring",
            "url": "https://g.live.com/0USSDMC_W5T/MacODSUInsiders",
            "version_key": "CFBundleShortVersionString",
            "binary_url_key": "UniversalPkgBinaryURL"
        },
        {
            "name": "Upcoming Production Ring",
            "url": "https://g.live.com/0USSDMC_W5T/StandaloneProductManifest",
            "version_key": "CFBundleShortVersionString",
            "binary_url_key": "UniversalPkgBinaryURL"
        },
        {
            "name": "Production Ring",
            "url": "https://g.live.com/0USSDMC_W5T/StandaloneProductManifest",
            "version_key": "CFBundleShortVersionString",
            "binary_url_key": "UniversalPkgBinaryURL"
        }
    ]
    for entry in xml_urls:
        version = extract_from_xml(entry["url"], entry["version_key"])
        version_changed = has_version_changed(entry["name"], version, existing_data)
        
        # Only fetch binary URL and calculate hashes if version has changed
        if version_changed:
            binary_url = extract_from_xml(entry["url"], entry["binary_url_key"])
            if not binary_url:
                logging.error(f"Binary URL not found for {entry['name']} in {entry['url']}")
                continue
                
            if not skip_sha_checks():
                logging.info(f"Fetching content and calculating hashes for {entry['name']}")
                content = fetch_url_content(binary_url)
                sha1 = calculate_hash(content, "sha1")
                sha256 = calculate_hash(content, "sha256")
            else:
                sha1 = "N/A"
                sha256 = "N/A"
        else:
            # Use existing data if version hasn't changed
            binary_url = existing_data[entry["name"]]["full_update_download"]
            sha1 = existing_data[entry["name"]]["full_update_sha1"]
            sha256 = existing_data[entry["name"]]["full_update_sha256"]
            
        package_data = {
            "name": entry["name"],
            "short_version": version,
            "full_update_download": binary_url,
            "full_update_sha1": sha1,
            "full_update_sha256": sha256,
            "version_changed": version_changed
        }
        packages.append(package_data)

    return packages

def xml_to_dict(element):
    """Convert XML element to ordered dictionary for JSON/YAML conversion."""
    result = OrderedDict()
    for child in element:
        # Handle nested elements
        if len(child):
            child_dict = xml_to_dict(child)
            if child.tag in result:
                # If the tag already exists, convert to list or append
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        else:
            # Handle text elements
            result[child.tag] = child.text or ""
    return result

def convert_to_json_yaml(xml_file):
    """Convert XML file to JSON and YAML formats."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Convert XML to ordered dictionary
        data = OrderedDict()
        data[root.tag] = xml_to_dict(root)
        
        # Generate file paths
        base_path = os.path.splitext(xml_file)[0]
        json_file = f"{base_path}.json"
        yaml_file = f"{base_path}.yaml"
        
        # Write JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Generated JSON file: {json_file}")
        
        # Set up YAML to preserve dictionary order
        class OrderedDumper(yaml.SafeDumper):
            pass
        
        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.Resolver.DEFAULT_MAPPING_TAG,
                data.items())
        
        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        
        # Write YAML file with order preserved
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, 
                     Dumper=OrderedDumper)
        logging.info(f"Generated YAML file: {yaml_file}")
        
        return True
    except Exception as e:
        logging.error(f"Error converting XML to JSON/YAML: {e}")
        return False

def get_package_order_priority(package_name):
    """
    Returns a numeric priority for package ordering.
    Lower numbers will appear first in the sorted list.
    """
    order_map = {
        "Production Ring": 1,
        "Upcoming Production Ring": 2,
        "Deferred Ring": 3,
        "Upcoming Deferred  Ring": 4,
        "Insider Ring": 5,
        "Rolling Out (Unknown Use)": 6,
        "App New Version (Unknown Use)": 7,
    }
    return order_map.get(package_name, 999)  # Default high number for unknown packages

def main():
    output_file = "latest_raw_files/macos_standalone_onedrive_all.xml"
    now = datetime.now().strftime("%B %d, %Y %I:%M %p %Z")
    
    # Load existing data if available
    existing_data = load_existing_data(output_file)
    
    # Fetch package data, reusing existing data where possible
    packages = fetch_package_data(existing_data)
    
    # Sort packages in the specified order
    packages.sort(key=lambda pkg: get_package_order_priority(pkg["name"]))
    
    # Check if any package has changed
    any_changes = any(package.get("version_changed", True) for package in packages)
    
    # Always generate a new XML file to update the global last_updated timestamp
    # Generate new XML 
    root = ET.Element("latest")
    global_last_updated = ET.SubElement(root, "last_updated")
    global_last_updated.text = now  # Always update the global last_updated field
    
    for package_data in packages:
        package_xml = generate_package_xml(package_data, existing_data, now)
        root.append(package_xml)

    # Convert to string and pretty-print
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    
    if any_changes:
        logging.info(f"Updated {output_file} with {len(packages)} packages - some packages were updated")
    else:
        logging.info(f"Updated {output_file} with {len(packages)} packages - only global timestamp was updated")
        
    # Convert XML to JSON and YAML formats
    convert_to_json_yaml(output_file)

if __name__ == "__main__":
    main()
