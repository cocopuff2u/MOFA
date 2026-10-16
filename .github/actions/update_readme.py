import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_latest_xml(file_path):
    logging.info(f"Parsing XML file: {file_path}")

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    logging.debug("XML file parsed successfully")

    # Extract global last_updated
    global_last_updated = root.find("last_updated").text.strip()
    logging.info(f"XML last_updated: {global_last_updated}")

    # Extract package details
    packages = {}
    for package in root.findall("package"):
        name = package.find("name").text.strip().lower()  # Store by lowercase name for easy access
        packages[name] = {
            "name": name,
            "application_id": package.find("application_id").text.strip(),
            "application_name": package.find("application_name").text.strip(),
            "short_version": package.find("short_version").text.strip(),
            "full_version": package.find("full_version").text.strip(),
            "last_updated": package.find("last_updated").text.strip(),
            "full_update_sha1": package.find("full_update_sha1").text.strip(),
            "app_only_update_download": package.find("app_only_update_download").text.strip(),
            "app_update_sha256": package.find("app_update_sha256").text.strip(),
            "app_update_sha1": package.find("app_update_sha1").text.strip(),
            "full_update_download": package.find("full_update_download").text.strip(),
            "full_update_sha256": package.find("full_update_sha256").text.strip(),
            "full_update_sha1": package.find("full_update_sha1").text.strip(),
            "min_os": package.find("min_os").text.strip() if package.find("min_os") is not None else "N/A",
        }
        # logging.debug(f"Extracted package: {packages[name]}") # Uncomment to see all package details

    return global_last_updated, packages

def parse_appstore_xml(file_path):
    logging.info(f"Parsing AppStore XML file: {file_path}")

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    logging.debug("AppStore XML file parsed successfully")

    # Extract global last_updated
    global_last_updated = root.find("last_updated").text.strip()
    logging.info(f"AppStore XML last_updated: {global_last_updated}")

    # Extract package details
    packages = {}
    for package in root.findall("package"):
        name = package.find("name").text.strip().lower()  # Store by lowercase name for easy access
        packages[name] = {
            "name": name,
            "application_name": package.find("application_name").text.strip(),
            "bundleid": package.find("bundleId").text.strip(),
            "currentVersionReleaseDate": package.find("currentVersionReleaseDate").text.strip(),
            "icon_image": package.find("icon_image").text.strip(),
            "minimumOsVersion": package.find("minimumOsVersion").text.strip(),
            "releaseNotes": package.find("releaseNotes").text.strip(),
            "version": package.find("version").text.strip(),
        }
        # logging.debug(f"Extracted AppStore package: {packages[name]}") # Uncomment to see all package details

    return global_last_updated, packages

def parse_onedrive_xml(file_path):
    logging.info(f"Parsing OneDrive XML file: {file_path}")

    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        logging.debug("OneDrive XML file parsed successfully")

        # Extract package details for all rings
        onedrive_data = {}
        for package in root.findall("package"):
            name = package.find("name").text.strip()
            ring_name = name.lower().replace(" ", "_")  # Convert name to a suitable key format
            
            onedrive_data[ring_name] = {
                "name": name,
                "short_version": package.find("short_version").text.strip(),
                "application_id": package.find("application_id").text.strip(),
                "application_name": package.find("application_name").text.strip(),
                "cfbundle_id": package.find("CFBundleVersion").text.strip(),
                "full_update_download": package.find("full_update_download").text.strip(),
                "full_update_sha1": package.find("full_update_sha1").text.strip(),
                "full_update_sha256": package.find("full_update_sha256").text.strip(),
                "last_updated": package.find("last_updated").text.strip(),
                # Adding minimal OS requirement though it may not exist in this XML
                "min_os": "NA", # Default value if not available
            }
        
        # Also keep the production ring at the top level for backward compatibility
        if "production_ring" in onedrive_data:
            for key, value in onedrive_data["production_ring"].items():
                onedrive_data[key] = value
        
        logging.info(f"OneDrive data extracted: {len(onedrive_data)} packages found")
        return onedrive_data

    except Exception as e:
        logging.error(f"Error parsing OneDrive XML: {e}")
        return {
            "name": "OneDrive",
            "short_version": "Unknown",
            "application_name": "OneDrive.app",
            "cfbundle_id": "com.microsoft.onedrive",
            "last_updated": "Unknown",
            "min_os": "Unknown",
            "full_update_download": "https://go.microsoft.com/fwlink/?linkid=823060",
            "full_update_sha1": "Unknown",
            "full_update_sha256": "Unknown"
        }

def parse_other_xml(file_path):
    """
    Parse the macOS "other" developer tools XML file (PowerShell, .NET SDKs,
    Azure tooling, sqlcmd, etc.). Package order from the XML is preserved.
    """
    logging.info(f"Parsing Other tools XML file: {file_path}")

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    logging.debug("Other tools XML file parsed successfully")

    # Extract global last_updated
    global_last_updated = root.find("last_updated").text.strip()
    logging.info(f"Other tools XML last_updated: {global_last_updated}")

    # Extract package details (keyed by lowercase name, insertion order preserved)
    packages = {}
    for package in root.findall("package"):
        name = package.find("name").text.strip()
        packages[name.lower()] = {
            "name": name,
            "application_id": package.find("application_id").text.strip(),
            "application_name": package.find("application_name").text.strip(),
            "cfbundle_version": package.find("CFBundleVersion").text.strip(),
            "short_version": package.find("short_version").text.strip(),
            "full_version": package.find("full_version").text.strip(),
            "last_updated": package.find("last_updated").text.strip(),
            "min_os": package.find("min_os").text.strip() if package.find("min_os") is not None else "N/A",
            "update_download": package.find("update_download").text.strip(),
            "latest_download": package.find("latest_download").text.strip(),
            "sha1": package.find("sha1").text.strip(),
            "sha256": package.find("sha256").text.strip(),
        }

    return global_last_updated, packages

def parse_edge_xml(file_path):
    """
    Parse the Edge XML file and extract details for the 'current' version.
    """
    logging.info(f"Parsing Edge XML file: {file_path}")

    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        logging.debug("Edge XML file parsed successfully")

        # Extract the 'current' version details
        current_version = None
        for version in root.findall("Version"):
            if version.find("Name").text.strip().lower() == "current":
                current_version = {
                    "name": "Microsoft Edge",
                    "short_version": version.find("Version").text.strip(),
                    "application_id": version.find("Application_ID").text.strip(),
                    "application_name": version.find("Application_Name").text.strip(),
                    "cfbundle_id": version.find("CFBundleVersion").text.strip(),
                    "full_update_download": version.find("Full_Update_Download").text.strip(),
                    "full_update_sha1": version.find("Full_Update_Sha1").text.strip(),
                    "full_update_sha256": version.find("Full_Update_Sha256").text.strip(),
                    "last_updated": version.find("Last_Update").text.strip(),
                }
                break

        if current_version:
            logging.info("Edge 'current' version details extracted successfully")
            return current_version
        else:
            logging.warning("No 'current' version found in Edge XML")
            return None

    except Exception as e:
        logging.error(f"Error parsing Edge XML: {e}")
        return None

def get_onedrive_package_detail(onedrive_data, ring_name, detail):
    """
    Get a specific detail from a specific OneDrive package/ring.
    
    Args:
        onedrive_data (dict): The OneDrive data structure containing all packages
        ring_name (str): The name of the ring (e.g. "production_ring", "insider_ring")
        detail (str): The detail to retrieve (e.g. "short_version", "full_update_download")
    
    Returns:
        str: The requested detail value or None if not found
    """
    ring_key = ring_name.lower().replace(" ", "_")
    detail = detail.lower()
    
    if ring_key in onedrive_data and detail in onedrive_data[ring_key]:
        return onedrive_data[ring_key][detail]
    else:
        # Fall back to top-level details for backward compatibility
        if detail in onedrive_data:
            return onedrive_data[detail]
        return None

def generate_ios_table(ios_packages):
    logging.info("Generating iOS AppStore table content")

    table_content = """
## iOS App Store

<sup>🟢 Updated <code>{ios_last_updated}</code>&nbsp;&nbsp;·&nbsp;&nbsp;Raw feed: <a href="latest_raw_files/ios_appstore_latest.xml"><kbd>XML</kbd></a> <a href="latest_raw_files/ios_appstore_latest.yaml"><kbd>YAML</kbd></a> <a href="latest_raw_files/ios_appstore_latest.json"><kbd>JSON</kbd></a>&nbsp;&nbsp;·&nbsp;&nbsp;refreshed every 4 hours</sup>

| **Application Name** | **Version** | **Bundle ID** | **Icon** |
|----------------------|-------------|---------------|----------|
"""

    for package_name in ios_packages:
        application_name = get_ios_package_detail(ios_packages, package_name, 'application_name')
        version = get_ios_package_detail(ios_packages, package_name, 'version')
        bundle_id = get_ios_package_detail(ios_packages, package_name, 'bundleid')  # Changed from 'bundleId'
        icon_image = get_ios_package_detail(ios_packages, package_name, 'icon_image')
        table_content += f"| {application_name} | `{version}` | `{bundle_id}` | <img src=\"{icon_image}\" alt=\"{application_name}\" width=\"40\"> |\n"

    logging.info("iOS AppStore table content generated successfully")
    return table_content

def generate_macos_table(macos_packages):
    logging.info("Generating macOS AppStore table content")

    table_content = """
## Mac App Store

<sup>🟢 Updated <code>{macos_last_updated}</code>&nbsp;&nbsp;·&nbsp;&nbsp;Raw feed: <a href="latest_raw_files/macos_appstore_latest.xml"><kbd>XML</kbd></a> <a href="latest_raw_files/macos_appstore_latest.yaml"><kbd>YAML</kbd></a> <a href="latest_raw_files/macos_appstore_latest.json"><kbd>JSON</kbd></a>&nbsp;&nbsp;·&nbsp;&nbsp;refreshed every 4 hours</sup>

| **Application Name** | **Version** | **Bundle ID** | **Icon** |
|----------------------|-------------|---------------|----------|
"""

    for package_name in macos_packages:
        application_name = get_macos_package_detail(macos_packages, package_name, 'application_name')
        version = get_macos_package_detail(macos_packages, package_name, 'version')
        bundle_id = get_macos_package_detail(macos_packages, package_name, 'bundleid')  # Changed from 'bundleId'
        icon_image = get_macos_package_detail(macos_packages, package_name, 'icon_image')
        table_content += f"| {application_name} | `{version}` | `{bundle_id}` | <img src=\"{icon_image}\" alt=\"{application_name}\" width=\"40\"> |\n"

    logging.info("macOS AppStore table content generated successfully")
    return table_content

def get_other_package_icon(package_name):
    """
    Map an "other" tools package name to its logo in .github/images.
    """
    name = package_name.lower()
    if "powershell" in name:
        return ".github/images/powershell.png"
    elif ".net sdk" in name:
        return ".github/images/dotnet.png"
    elif "bicep" in name:
        return ".github/images/bicep.png"
    elif "sqlcmd" in name:
        return ".github/images/sqlcmd.png"
    elif name.startswith("az") or "azure" in name:
        return ".github/images/azure.png"
    else:
        return ".github/images/pkg-icon.png"

def generate_other_table(other_packages):
    logging.info("Generating Other tools table content")

    table_content = """
## Other Microsoft apps

<sup>Microsoft tools outside the Office suite, from GitHub releases, Microsoft's CDN or Homebrew. Some are Homebrew-only; the versions below are the latest official releases.</sup>

<sup>🟢 Updated <code>{other_last_updated}</code>&nbsp;&nbsp;·&nbsp;&nbsp;Raw feed: <a href="latest_raw_files/macos_other_latest.xml"><kbd>XML</kbd></a> <a href="latest_raw_files/macos_other_latest.yaml"><kbd>YAML</kbd></a> <a href="latest_raw_files/macos_other_latest.json"><kbd>JSON</kbd></a>&nbsp;&nbsp;·&nbsp;&nbsp;refreshed every 4 hours</sup>

| **Product Package** | **Bundle Information** | **Download** |
|----------------------|----------------------|--------------|
"""

    # Direct downloads first, Homebrew-only packages grouped at the bottom
    direct_packages = [p for p in other_packages.values() if p["latest_download"].startswith("http")]
    brew_packages = [p for p in other_packages.values() if not p["latest_download"].startswith("http")]

    for package in direct_packages + brew_packages:
        name = package["name"]
        icon = get_other_package_icon(name)
        download = package["latest_download"]

        if download.startswith("http"):
            download_cell = f"<a href=\"{download}\"><img src=\"{icon}\" alt=\"Download Image\" width=\"80\"></a>"
        else:
            # Not a direct download (e.g. installed via Homebrew)
            download_cell = f"<img src=\"{icon}\" alt=\"{name}\" width=\"80\"><br>`{download}`"

        table_content += (
            f"| **{name}**<br><br>_**Last Update:** `{package['last_updated']}`_<br> "
            f"| **Version:**<br>`{package['short_version']}` "
            f"| {download_cell} |\n"
        )

    # SHA256 table for packages with direct downloads
    table_content += """
### SHA256 hashes

| **Product Package** | **Download** | **SHA256** |
|----------------------|-----------------|------------|
"""

    for package_key, package in other_packages.items():
        if not package["latest_download"].startswith("http"):
            continue
        name = package["name"]
        icon = get_other_package_icon(name)
        table_content += (
            f"| **{name}** "
            f"| <a href=\"{package['latest_download']}\"><img src=\"{icon}\" alt=\"Download Image\" width=\"80\"></a> "
            f"| `{package['sha256']}` |\n"
        )

    logging.info("Other tools table content generated successfully")
    return table_content

def generate_readme_content(global_last_updated, packages, ios_packages, macos_packages):
    logging.info("Generating README content")

    # Set timezone to US/Eastern (EST/EDT)
    eastern = pytz.timezone('US/Eastern')

    # Get the current time in UTC and convert to EST
    current_time = datetime.now(pytz.utc).astimezone(eastern).strftime("%B %d, %Y %I:%M %p %Z")
    logging.debug(f"Current time (EST): {current_time}")

    ios_table = generate_ios_table(ios_packages).format(ios_last_updated=ios_last_updated)
    macos_table = generate_macos_table(macos_packages).format(macos_last_updated=macos_last_updated)
    other_table = generate_other_table(other_packages).format(other_last_updated=other_last_updated)

    content = f"""<div align="center">

<a href="https://mofa.cocolabs.dev"><img src=".github/branding/github-readme-banner-2400x600.png" alt="MOFA - Microsoft Overview Feed For Apple" width="100%"></a>

<br>

<a href="https://mofa.cocolabs.dev"><img src="https://img.shields.io/badge/website-mofa.cocolabs.dev-037F8C?style=for-the-badge&labelColor=0B2E36" alt="Website"></a> <a href="https://github.com/cocopuff2u/MOFA/stargazers"><img src="https://img.shields.io/github/stars/cocopuff2u/MOFA?style=for-the-badge&color=046672&labelColor=0B2E36" alt="GitHub stars"></a> <a href="https://mofa.cocolabs.dev/standalone_apps/standalone_raw_feeds_en#rss-feeds"><img src="https://img.shields.io/badge/RSS-11_feeds-BF1304?style=for-the-badge&labelColor=0B2E36" alt="RSS feeds"></a> <a href="https://macadmins.org/slack"><img src="https://img.shields.io/badge/Mac_Admins-Slack-6F890B?style=for-the-badge&labelColor=0B2E36" alt="Mac Admins Slack"></a>

</div>

**MOFA** tracks every Microsoft app on macOS and iOS: current, preview and beta versions, SHA hashes, update and CVE history, and direct download links to Microsoft's CDN. Everything is scraped from Microsoft and Apple on a schedule and published here as XML, YAML and JSON, so you can read the tables below or point your own tooling at the feeds.

> **Prefer a website?** All of this, plus guides, configuration profiles and repair tools, is at **[mofa.cocolabs.dev](https://mofa.cocolabs.dev)**. The site is built from the same feeds, so it is never behind this README.

## What's in here

| Section | What you get | On the website |
|---|---|---|
| [Standalone packages](#standalone-packages) | Office, Teams, OneDrive, Edge, Defender, Intune, Windows App and more, with SHA256 hashes and the last builds for older macOS | [Current](https://mofa.cocolabs.dev/standalone_apps/standalone_current_version_en) · [Preview](https://mofa.cocolabs.dev/standalone_apps/standalone_preview_version_en) · [Beta](https://mofa.cocolabs.dev/standalone_apps/standalone_beta_version_en) · [Update history](https://mofa.cocolabs.dev/standalone_apps/standalone_update_history_en) · [CVE history](https://mofa.cocolabs.dev/standalone_apps/standalone_cve_history_en) |
| [Other Microsoft apps](#other-microsoft-apps) | PowerShell, .NET SDKs, Azure tooling, Bicep and sqlcmd | [Other apps](https://mofa.cocolabs.dev/standalone_apps/macos_standalone_other_readme) |
| [Mac App Store](#mac-app-store) | Versions and bundle IDs for Microsoft's Mac App Store apps | [Mac App Store](https://mofa.cocolabs.dev/macos_appstore/macos_appstore_current_version) |
| [iOS App Store](#ios-app-store) | Versions and bundle IDs for Microsoft's iOS apps | [iOS App Store](https://mofa.cocolabs.dev/ios_appstore/ios_appstore_current_version) |
| [Raw feeds](#raw-feeds) | Every dataset as XML, YAML and JSON, plus RSS | [Raw feeds](https://mofa.cocolabs.dev/standalone_apps/standalone_raw_feeds_en) |
| [Tools and guides](#tools-and-guides) | Repair tools, `.mobileconfig` profiles, preference keys, how-to guides | [MacOS Tools](https://mofa.cocolabs.dev/macos_tools/microsoft_office_repair_tools) |

## Raw feeds

Machine-readable copies of everything on this page live in [`latest_raw_files/`](latest_raw_files). Each dataset is written in three formats and refreshed on the schedule shown next to its table.

| Dataset | | | |
|---|---|---|---|
| Standalone packages, current | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_latest.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_latest.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_latest.json) |
| Standalone packages, preview | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_preview.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_preview.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_preview.json) |
| Standalone packages, beta | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_beta.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_beta.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_beta.json) |
| Office update history | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_update_history.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_update_history.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_update_history.json) |
| Office CVE history | [<kbd>XML</kbd>](latest_raw_files/mac_standalone_cve_history.xml) | [<kbd>YAML</kbd>](latest_raw_files/mac_standalone_cve_history.yaml) | [<kbd>JSON</kbd>](latest_raw_files/mac_standalone_cve_history.json) |
| Teams update history | [<kbd>XML</kbd>](latest_raw_files/teams_update_history.xml) | [<kbd>YAML</kbd>](latest_raw_files/teams_update_history.yaml) | [<kbd>JSON</kbd>](latest_raw_files/teams_update_history.json) |
| OneDrive, all rings | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_onedrive_all.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_onedrive_all.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_onedrive_all.json) |
| Edge, all channels | [<kbd>XML</kbd>](latest_raw_files/macos_standalone_edge_all.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_standalone_edge_all.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_standalone_edge_all.json) |
| Other Microsoft apps | [<kbd>XML</kbd>](latest_raw_files/macos_other_latest.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_other_latest.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_other_latest.json) |
| Mac App Store | [<kbd>XML</kbd>](latest_raw_files/macos_appstore_latest.xml) | [<kbd>YAML</kbd>](latest_raw_files/macos_appstore_latest.yaml) | [<kbd>JSON</kbd>](latest_raw_files/macos_appstore_latest.json) |
| iOS App Store | [<kbd>XML</kbd>](latest_raw_files/ios_appstore_latest.xml) | [<kbd>YAML</kbd>](latest_raw_files/ios_appstore_latest.yaml) | [<kbd>JSON</kbd>](latest_raw_files/ios_appstore_latest.json) |

<sup>RSS: one feed per standalone app in [`latest_raw_files/macos_standalone_rss/`](latest_raw_files/macos_standalone_rss). Links on the [website](https://mofa.cocolabs.dev/standalone_apps/standalone_raw_feeds_en#rss-feeds).</sup>

## Standalone packages

<sup>Direct links to Microsoft's CDN. A link always downloads the newest build Microsoft offers, so the version shown is the one available at the time of the last update.</sup>

<sup>🟢 Updated <code>{global_last_updated}</code>&nbsp;&nbsp;·&nbsp;&nbsp;Raw feed: <a href="latest_raw_files/macos_standalone_latest.xml"><kbd>XML</kbd></a> <a href="latest_raw_files/macos_standalone_latest.yaml"><kbd>YAML</kbd></a> <a href="latest_raw_files/macos_standalone_latest.json"><kbd>JSON</kbd></a>&nbsp;&nbsp;·&nbsp;&nbsp;refreshed every 1 hour</sup>

| **Product Package** | **Bundle Information** | **Download** |
|----------------------|----------------------|--------------|
| **Microsoft** <sup>365/2021/2024</sup> **Office Suite Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac" style="text-decoration: none;"><small>_Release Notes_</small></a><br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Defender Shim, and MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.office` | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Microsoft** <sup>365/2021/2024</sup> **BusinessPro Suite Installer**<br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Defender Shim, and MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.office` | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Word** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Word', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Word', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Word', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.word` | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/Word.png" alt="Download Image" width="80"></a> |
| **Word** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Word', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Word', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Word', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.word` | <a href="{get_standalone_package_detail(packages, 'Word', 'app_only_update_download')}"><img src=".github/images/Word.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Excel', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Excel', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Excel', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.excel` | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/Excel.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Excel', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Excel', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Excel', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.excel` | <a href="{get_standalone_package_detail(packages, 'Excel', 'app_only_update_download')}"><img src=".github/images/Excel.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'PowerPoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.powerpoint` | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PowerPoint.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'PowerPoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.powerpoint` | <a href="{get_standalone_package_detail(packages, 'PowerPoint', 'app_only_update_download')}"><img src=".github/images/PowerPoint.png" alt="Download Image" width="80"></a> |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Outlook', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.outlook` | <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook.png" alt="Download Image" width="80"></a>|
| **Outlook** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Outlook', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.outlook` | <a href="{get_standalone_package_detail(packages, 'Outlook', 'app_only_update_download')}"><img src=".github/images/Outlook.png" alt="Download Image" width="80"></a>|
| **OneNote** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'OneNote', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.onenote.mac` | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote.png" alt="Download Image" width="80"></a> |
| **OneNote** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'OneNote', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.onenote.mac` | <a href="{get_standalone_package_detail(packages, 'OneNote', 'app_only_update_download')}"><img src=".github/images/OneNote.png" alt="Download Image" width="80"></a> |
| **OneDrive Standalone Installer** <sup>(Production Ring)</sup> <br><a href="https://support.microsoft.com/en-us/office/onedrive-release-notes-845dcf18-f921-435e-bf28-4e24b95e5fc0#OSVersion=Mac" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'last_updated')}`_<br> | **Version:**<br>`{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'short_version')}`<br><br>**Min OS:**<br>`NA`<br><br>**CFBundle ID:**<br>`com.microsoft.OneDrive` | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive.png" alt="Download Image" width="80"></a> |
| **Skype for Business Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/follow-the-latest-updates-in-skype-for-business-cece9f93-add1-4d93-9a38-56cc598e5781?ui=en-us&rs=en-us&ad=us" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Skype', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Skype', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Skype', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.SkypeForBusiness` | <a href="{get_standalone_package_detail(packages, 'Skype', 'app_only_update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="80"></a> |
| **Teams Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/what-s-new-in-microsoft-teams-d7092a6d-c896-424c-b362-a472d5f105de" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Teams', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Teams', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Teams', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.teams2` | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/Teams.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal Standalone Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Intune', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Intune', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Intune', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.CompanyPortalMac` | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal App Only Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a> <sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Intune', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Intune', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Intune', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.CompanyPortalMac` | <a href="{get_standalone_package_detail(packages, 'Intune', 'app_only_update_download')}"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **Edge** <sup>_(Current Channel)_</sup><br><a href="https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Edge', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Edge', 'short_version')}`<br><br>**Min OS:**<br>`11.0`<br><br>**CFBundle ID:**<br>`com.microsoft.edgemac` | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="80"></a>|
| **Defender for Endpoint Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender For Endpoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender For Endpoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav` | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> |
| **Defender for Consumers Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender For Consumers', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender For Consumers', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender For Consumers', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav` | <a href="https://go.microsoft.com/fwlink/?linkid=2247001"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> |
| **Defender SHIM Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender Shim', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender Shim', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender Shim', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav.shim` | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'app_only_update_download')}"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> |
| **Windows App Standalone Installer** <sup>_(Remote Desktop <img src=".github/images/microsoft-remote-desktop-logo.png" alt="Remote Desktop" width="15" style="vertical-align: middle; display: inline-block;" />)_</sup><br><a href="https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Windows App', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.rdc.macos` | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> |
| **Windows App Only Installer** <sup>_(Remote Desktop <img src=".github/images/microsoft-remote-desktop-logo.png" alt="Remote Desktop" width="15" style="vertical-align: middle; display: inline-block;" />)_</sup><br><a href="https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos" style="text-decoration: none;"><small>_Release Notes_</small></a> <sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Windows App', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.rdc.macos` | <a href="{get_standalone_package_detail(packages, 'Windows App', 'app_only_update_download')}"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> |
| **Visual Studio Code Standalone Installer**<br><a href="https://code.visualstudio.com/updates/" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Visual', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Visual', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Visual', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.VSCode` | <a href="https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal-dmg"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="80"></a>|
| **Microsoft 365 Copilot**<br><a href="https://learn.microsoft.com/en-us/copilot/microsoft-365/release-notes?tabs=all" style="text-decoration: none;"><small>_Release Notes_</small></a><br><sub>_(Transitioning into the Copilot app below)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Copilot', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Copilot', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Copilot', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.m365copilot` | <a href="https://go.microsoft.com/fwlink/?linkid=2325438"><img src=".github/images/Copilot.png" alt="Download Image" width="80"></a>|
| **Microsoft Copilot** <sup>_(Copilot App)_</sup><br><a href="https://support.microsoft.com/en-us/microsoft-365-copilot/the-microsoft-365-app-transition-to-the-microsoft-365-copilot-app" style="text-decoration: none;"><small>_Transition Notes_</small></a><br><sub>_(Replaces Microsoft 365 Copilot; updated by EdgeUpdater, not MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Copilot App', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Copilot App', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Copilot App', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.m365copilot` | <a href="https://go.microsoft.com/fwlink/?linkid=2325114"><img src=".github/images/Copilot_App.png" alt="Download Image" width="80"></a>|
| **AutoUpdate Standalone Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-history-microsoft-autoupdate" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'MAU', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'MAU', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'MAU', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.autoupdate` | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="80"></a>|
| **Licensing Helper Tool Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.licensinghelper` | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="80"></a>|
| **Quick Assist Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Quick Assist', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Quick Assist', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Quick Assist', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.quickassist` | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="80"></a>|
| **Remote Help Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Remote Help', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Remote Help', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Remote Help', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.remotehelp` | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'full_update_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="80"></a>|

### SHA256 hashes

| **Product Package** | **Download** | **SHA256** |
|----------------------|-----------------|------------|
| **Microsoft Office Suite** | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'full_update_sha256')}` |
| **Microsoft BusinessPro Suite** | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'full_update_sha256')}` |
| **Word Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/Word.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Word', 'full_update_sha256')}` |
| **Word App Only** | <a href="{get_standalone_package_detail(packages, 'Word', 'app_only_update_download')}"><img src=".github/images/Word.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Word', 'app_update_sha256')}` |
| **Excel Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/Excel.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Excel', 'full_update_sha256')}` |
| **Excel App Only** | <a href="{get_standalone_package_detail(packages, 'Excel', 'app_only_update_download')}"><img src=".github/images/Excel.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Excel', 'app_update_sha256')}` |
| **PowerPoint Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PowerPoint.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'PowerPoint', 'full_update_sha256')}` |
| **PowerPoint App Only** | <a href="{get_standalone_package_detail(packages, 'PowerPoint', 'app_only_update_download')}"><img src=".github/images/PowerPoint.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'PowerPoint', 'app_update_sha256')}` |
| **Outlook Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Outlook', 'full_update_sha256')}` |
| **Outlook App Only** | <a href="{get_standalone_package_detail(packages, 'Outlook', 'app_only_update_download')}"><img src=".github/images/Outlook.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Outlook', 'app_update_sha256')}` |
| **OneNote Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'OneNote', 'full_update_sha256')}` |
| **OneNote App Only** | <a href="{get_standalone_package_detail(packages, 'OneNote', 'app_only_update_download')}"><img src=".github/images/OneNote.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'OneNote', 'app_update_sha256')}` |
| **OneDrive** | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive.png" alt="Download Image" width="80"></a> | `{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'full_update_sha256')}` |
| **Skype for Business** | <a href="{get_standalone_package_detail(packages, 'Skype', 'app_only_update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Skype', 'full_update_sha256')}` |
| **Teams** | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/Teams.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Teams', 'full_update_sha256')}` |
| **Intune Company Portal Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Intune', 'full_update_sha256')}` |
| **Intune Company Portal App Only** | <a href="{get_standalone_package_detail(packages, 'Intune', 'app_only_update_download')}"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Intune', 'app_update_sha256')}` |
| **Edge** | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Edge', 'full_update_sha256')}` |
| **Defender for Endpoint** | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'full_update_sha256')}` |
| **Defender for Consumers** | <a href="https://go.microsoft.com/fwlink/?linkid=2247001"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender For Consumers', 'full_update_sha256')}` |
| **Defender SHIM** | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'app_only_update_download')}"><img src=".github/images/defender.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender Shim', 'full_update_sha256')}` |
| **Windows App Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Windows App', 'full_update_sha256')}` |
| **Windows App Only** | <a href="{get_standalone_package_detail(packages, 'Windows App', 'app_only_update_download')}"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Windows App', 'app_update_sha256')}` |
| **Visual Studio Code** | <a href="https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal-dmg"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Visual', 'full_update_sha256')}` |
| **Microsoft 365 Copilot** | <a href="https://go.microsoft.com/fwlink/?linkid=2325438"><img src=".github/images/Copilot.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Copilot', 'full_update_sha256')}` |
| **Microsoft Copilot** <sup>_(Copilot App)_</sup> | <a href="https://go.microsoft.com/fwlink/?linkid=2325114"><img src=".github/images/Copilot_App.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Copilot App', 'full_update_sha256')}` |
| **AutoUpdate** | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'MAU', 'full_update_sha256')}` |
| **Licensing Helper Tool** | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_sha256')}` |
| **Quick Assist** | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_sha256')}` |
| **Remote Help** | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'full_update_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Remote Help', 'full_update_sha256')}` |

<sup>Verify a download with <code>shasum -a 256 /path/to/file.pkg</code> and compare it to the table. Guide: [How to SHA256](guides/How_To_SHA256.md). Apps without their own release notes follow the Office suite's. SHA1 and preview/beta hashes are on the [website](https://mofa.cocolabs.dev/standalone_apps/standalone_sha256_hashes_en).</sup>

### Last supported versions

<sup>The final build of the Office suite for each macOS that Microsoft no longer supports.</sup>

| **Last Supported MacOS** | **File Name** | **Version** | **Download** |
|---------------------------|----------------|-------------|--------------|
| macOS 13 Ventura<br><img src=".github/images/MacOS_Ventura_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.101` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.101.25091314_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 13 Ventura<br><img src=".github/images/MacOS_Ventura_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.101` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.101.25091314_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 12 Monterey<br><img src=".github/images/MacOS_Monterey_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.88` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.88.24081116_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 12 Monterey<br><img src=".github/images/MacOS_Monterey_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.88` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.88.24081116_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 11 Big Sur<br><img src=".github/images/MacOS_BigSur_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.77` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.77.23091003_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 11 Big Sur<br><img src=".github/images/MacOS_BigSur_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.77` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.77.23091003_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 10.15 Catalina<br><img src=".github/images/MacOS_Catalina_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.66` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_Office_16.66.22100900_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 10.15 Catalina<br><img src=".github/images/MacOS_Catalina_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.66` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_Office_16.66.22100900_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |


<sup>Related: <a href="https://mofa.cocolabs.dev/standalone_apps/standalone_update_history_en"><kbd>Office update history</kbd></a> <a href="https://mofa.cocolabs.dev/standalone_apps/standalone_cve_history_en"><kbd>CVE history</kbd></a> <a href="https://mofa.cocolabs.dev/standalone_apps/teams_update_history_en"><kbd>Teams update history</kbd></a> <a href="https://mofa.cocolabs.dev/standalone_apps/standalone_last_supported_versions_en"><kbd>Last supported versions</kbd></a> <a href="https://learn.microsoft.com/en-us/microsoft-365-apps/updates/overview-update-channels"><kbd>Microsoft update channels</kbd></a></sup>

{other_table}

{macos_table}

{ios_table}

## Tools and guides

These moved to the website, where they are easier to browse and kept current. The source files still live in this repository.

| | |
|---|---|
| **[Office repair tools](https://mofa.cocolabs.dev/macos_tools/microsoft_office_repair_tools)** | Reset and repair scripts for Office, Outlook, OneDrive, Teams and friends, including the archived Office Reset packages in [`office_reset_tools/`](office_reset_tools). |
| **[Community scripts](https://mofa.cocolabs.dev/macos_tools/community_scripts)** | Scripts shared by Mac admins for installing, updating and troubleshooting Microsoft apps. |
| **[Configuration profiles](https://mofa.cocolabs.dev/macos_tools/preconfigured_profiles)** | Ready-to-deploy `.mobileconfig` files for Microsoft AutoUpdate deadlines and privacy prompts. Source in [`mobileconfig_profiles/`](mobileconfig_profiles). |
| **[Preference keys](https://mofa.cocolabs.dev/macos_tools/profile_breakdown)** | How Office plist keys work, with the community preference list and Microsoft's documentation. |
| **Guides** | [How to plist](guides/How_To_plist.md) · [How to SHA256](guides/How_To_SHA256.md) |

## Get involved

MOFA is built in the open by Mac admins, for Mac admins. You don't need to be a developer to help.

| | |
|---|---|
| 🐛 **[Report an issue](https://github.com/cocopuff2u/MOFA/issues)** | A wrong version, a dead link, a missing app. Issues are the fastest way to get it fixed. |
| 💡 **[Suggest something](https://github.com/cocopuff2u/MOFA/discussions)** | New feeds, new apps to track, or anything that would make MOFA more useful. |
| 🔀 **Send a pull request** | Fork the repo, make your change and open a PR. The generators live in [`.github/actions/`](.github/actions). |
| 💬 **[Mac Admins Slack](https://macadmins.org/slack)** | Say hi to `cocopuff2u`, or join `#microsoft-office`, `#microsoft-autoupdate`, `#microsoft-intune`, `#microsoft-windows-app` and `#microsoft-teams`. |
| ⭐ **[Star the repo](https://github.com/cocopuff2u/MOFA)** | It helps other admins find the project. |
| ☕ **[Buy me a coffee](https://www.buymeacoffee.com/cocopuff2u)** | Covers the domain and hosting; anything left over goes back to the Mac Admins community. |

## Thanks

MOFA picks up where the much-missed [MacAdmins.software](https://macadmins.software) left off. Special thanks to [Paul Bowden](https://github.com/pbowden-msft) for years of exceptional work for the Mac Admins community, and to everyone who has [contributed](https://mofa.cocolabs.dev/about_support/team) since.

Useful background reading: [Microsoft versioning explained](https://macmule.com/2018/09/24/microsoft-office-for-mac-changes-versioning-shenanigans/) · [Deployment options for Office for Mac](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deployment-options-for-office-for-mac) · [Deploying from the Mac App Store](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deploy-mac-app-store) · [Jamf: managing Microsoft Office](https://learn.jamf.com/en-US/bundle/technical-paper-microsoft-office-current/page/User_Experience_Configuration.html)

<sub>Microsoft 365, Office 365, Excel, PowerPoint, Outlook, OneDrive, OneNote, Teams and Edge are trademarks of Microsoft Corporation. Mac, macOS and iOS are trademarks of Apple Inc. Other names and brands may be claimed as the property of their respective owners. MOFA is a community project and is not affiliated with Microsoft or Apple.</sub>
"""
    logging.info("README content generated successfully")

    return content

def overwrite_readme(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)
    print(f"README.md has been overwritten.")

def get_standalone_package_detail(packages, package_name, detail):
    package_name = package_name.lower()
    detail = detail.lower()

    if package_name in packages and detail in packages[package_name]:
        return packages[package_name][detail]
    else:
        return None

def get_ios_package_detail(ios_packages, package_name, detail):
    package_name = package_name.lower()
    detail = detail.lower()

    if package_name in ios_packages and detail in ios_packages[package_name]:
        return ios_packages[package_name][detail]
    else:
        return None

def get_macos_package_detail(macos_packages, package_name, detail):
    package_name = package_name.lower()
    detail = detail.lower()

    if package_name in macos_packages and detail in macos_packages[package_name]:
        return macos_packages[package_name][detail]
    else:
        return None

def get_onedrive_detail(packages, package_name, detail):
    package_name = package_name.lower()
    detail = detail.lower()
    
    if package_name in packages and detail in packages[package_name]:
        return packages[package_name][detail]
    else:
        return None

if __name__ == "__main__":
    # Define file paths
    xml_file_path = "latest_raw_files/macos_standalone_latest.xml"  # Update this path if the file is located elsewhere
    ios_appstore_xml_path = "latest_raw_files/ios_appstore_latest.xml"
    macos_appstore_xml_path = "latest_raw_files/macos_appstore_latest.xml"
    onedrive_xml_path = "latest_raw_files/macos_standalone_onedrive_all.xml"
    edge_xml_path = "latest_raw_files/macos_standalone_edge_all.xml"  # Update this path if the file is located elsewhere
    other_xml_path = "latest_raw_files/macos_other_latest.xml"
    readme_file_path = "README.md"

    # Parse the XML and generate content
    global_last_updated, packages = parse_latest_xml(xml_file_path)
    ios_last_updated, ios_packages = parse_appstore_xml(ios_appstore_xml_path)
    macos_last_updated, macos_packages = parse_appstore_xml(macos_appstore_xml_path)
    other_last_updated, other_packages = parse_other_xml(other_xml_path)
    
    # Parse OneDrive XML
    onedrive_data = parse_onedrive_xml(onedrive_xml_path)
    
    # Update the OneDrive package information with data from the specific XML
    packages["onedrive"] = onedrive_data
    
    # Parse Edge XML
    edge_data = parse_edge_xml(edge_xml_path)
    if edge_data:
        packages["edge"] = edge_data

    # Merge packages
    packages.update(ios_packages)
    packages.update(macos_packages)

    readme_content = generate_readme_content(global_last_updated, packages, ios_packages, macos_packages)

    # Overwrite the README file
    overwrite_readme(readme_file_path, readme_content)
