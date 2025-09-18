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
## <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"></a> Microsoft iOS AppStore Packages

<sup>_Last Updated: <code style="color : mediumseagreen">{ios_last_updated}</code> [**_Raw XML_**](latest_raw_files/ios_appstore_latest.xml) [**_Raw YAML_**](latest_raw_files/ios_appstore_latest.yaml) [**_Raw JSON_**](latest_raw_files/ios_appstore_latest.json) (Automatically Updated every 4 hours)_</sup>

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
## <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"></a> Microsoft MacOS AppStore Packages

<sup>_Last Updated: <code style="color : mediumseagreen">{macos_last_updated}</code> [**_Raw XML_**](latest_raw_files/macos_appstore_latest.xml) [**_Raw YAML_**](latest_raw_files/macos_appstore_latest.yaml) [**_Raw JSON_**](latest_raw_files/macos_appstore_latest.json) (Automatically Updated every 4 hours)_</sup>

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

def generate_readme_content(global_last_updated, packages, ios_packages, macos_packages):
    logging.info("Generating README content")

    # Set timezone to US/Eastern (EST/EDT)
    eastern = pytz.timezone('US/Eastern')

    # Get the current time in UTC and convert to EST
    current_time = datetime.now(pytz.utc).astimezone(eastern).strftime("%B %d, %Y %I:%M %p %Z")
    logging.debug(f"Current time (EST): {current_time}")

    ios_table = generate_ios_table(ios_packages).format(ios_last_updated=ios_last_updated)
    macos_table = generate_macos_table(macos_packages).format(macos_last_updated=macos_last_updated)

    content = f"""# **MOFA**
**M**icrosoft **O**verview **F**eed for **A**pple

<img src=".github/images/logo_Mofa_NoBackground.png" alt="MOFA Image" width="200">

Welcome to the **MOFA** repository! This resource offers Microsoft Office downloads for macOS, comprehensive data feeds for all iOS, Mac App Store, and other Microsoft apps, along with tools and documentation links to help Mac admins manage and repair Microsoft products on Apple platforms. Feeds are automatically updated from XML and JSON links directly from Microsoft.

Building on the legacy of the now-defunct [**MacAdmins.software**](https://macadmins.software), MOFA provides a comprehensive and up-to-date solution. Special thanks to [**Paul Bowden**](https://github.com/pbowden-msft) for his exceptional contributions to the Mac Admins community.

We welcome community contributions—fork the repository, ask questions, or share insights to help keep this resource accurate and useful for everyone. Check out the user-friendly website version below for an easier browsing experience!

<div align="center">

<table>
  <tr>
    <th>🌟 Explore the MOFA Website 🌟</th>
    <th>⭐ Support the Project – Give it a Star! ⭐</th>
  </tr>
  <tr>
    <td align="center">🌐 <strong>Visit:</strong> <a href="https://mofa.cocolabs.dev">mofa.cocolabs.dev</a> 🌐</td>
    <td align="center">
      <a href="https://github.com/cocopuff2u/mofa">
        <img src="https://img.shields.io/github/stars/cocopuff2u/mofa" alt="GitHub Repo Stars">
      </a>
    </td>
  </tr>
</table>

</div>



## <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"></a> Microsoft Standalone Packages

<sup>All links below direct to Microsoft's official Content Delivery Network (CDN).</sup>
<sup>The links provided will always download the latest version offered by Microsoft. However, the version information listed below reflects the version available at the time of this update.</sup>

<sup>_Last Updated: <code style="color : mediumseagreen">{global_last_updated}</code> [**_Raw XML_**](latest_raw_files/macos_standalone_latest.xml) [**_Raw YAML_**](latest_raw_files/macos_standalone_latest.yaml) [**_Raw JSON_**](latest_raw_files/macos_standalone_latest.json) (Automatically Updated every 1 hour)_</sup>

| **Product Package** | **Bundle Information** | **Download** |
|----------------------|----------------------|--------------|
| **Microsoft** <sup>365/2021/2024</sup> **Office Suite Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac" style="text-decoration: none;"><small>_Release Notes_</small></a><br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, and MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.office` | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Microsoft** <sup>365/2021/2024</sup> **BusinessPro Suite Installer**<br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Defender Shim, and MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.office` | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Word** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Word', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Word', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Word', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.word` | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> |
| **Word** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Word', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Word', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Word', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.word` | <a href="{get_standalone_package_detail(packages, 'Word', 'app_only_update_download')}"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Excel', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Excel', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Excel', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.excel` | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Excel', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Excel', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Excel', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.excel` | <a href="{get_standalone_package_detail(packages, 'Excel', 'app_only_update_download')}"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'PowerPoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.powerpoint` | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'PowerPoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'PowerPoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.powerpoint` | <a href="{get_standalone_package_detail(packages, 'PowerPoint', 'app_only_update_download')}"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Outlook', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.outlook` | <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a>|
| **Outlook** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Outlook', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Outlook', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.outlook` | <a href="{get_standalone_package_detail(packages, 'Outlook', 'app_only_update_download')}"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a>|
| **OneNote** <sup>365/2021/2024</sup> **Standalone Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'OneNote', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.onenote.mac` | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> |
| **OneNote** <sup>365/2021/2024</sup> **App Only Installer** <br><sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'OneNote', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'OneNote', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.onenote.mac` | <a href="{get_standalone_package_detail(packages, 'OneNote', 'app_only_update_download')}"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> |
| **OneDrive Standalone Installer** <sup>(Production Ring)</sup> <br><a href="https://support.microsoft.com/en-us/office/onedrive-release-notes-845dcf18-f921-435e-bf28-4e24b95e5fc0#OSVersion=Mac" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'last_updated')}`_<br> | **Version:**<br>`{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'short_version')}`<br><br>**Min OS:**<br>`NA`<br><br>**CFBundle ID:**<br>`com.microsoft.OneDrive` | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive_512x512x32.png" alt="Download Image" width="80"></a> |
| **Skype for Business Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/follow-the-latest-updates-in-skype-for-business-cece9f93-add1-4d93-9a38-56cc598e5781?ui=en-us&rs=en-us&ad=us" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Skype', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Skype', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Skype', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.SkypeForBusiness` | <a href="{get_standalone_package_detail(packages, 'Skype', 'app_only_update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="80"></a> |
| **Teams Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/what-s-new-in-microsoft-teams-d7092a6d-c896-424c-b362-a472d5f105de" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Teams', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Teams', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Teams', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.teams2` | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/teams_512x512x32.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal Standalone Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Intune', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Intune', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Intune', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.CompanyPortalMac` | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal App Only Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a> <sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Intune', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Intune', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Intune', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.CompanyPortalMac` | <a href="{get_standalone_package_detail(packages, 'Intune', 'app_only_update_download')}"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **Edge** <sup>_(Current Channel)_</sup><br><a href="https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Edge', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Edge', 'short_version')}`<br><br>**Min OS:**<br>`11.0`<br><br>**CFBundle ID:**<br>`com.microsoft.edgemac` | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="80"></a>|
| **Defender for Endpoint Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender For Endpoint', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender For Endpoint', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav` | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Defender for Consumers Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender For Consumers', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender For Consumers', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender For Consumers', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav` | <a href="https://go.microsoft.com/fwlink/?linkid=2247001"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Defender SHIM Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Defender Shim', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Defender Shim', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Defender Shim', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.wdav.shim` | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'app_only_update_download')}"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Windows App Standalone Installer** <sup>_(Remote Desktop <img src=".github/images/microsoft-remote-desktop-logo.png" alt="Remote Desktop" width="15" style="vertical-align: middle; display: inline-block;" />)_</sup><br><a href="https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Windows App', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.rdc.macos` | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> |
| **Windows App Only Installer** <sup>_(Remote Desktop <img src=".github/images/microsoft-remote-desktop-logo.png" alt="Remote Desktop" width="15" style="vertical-align: middle; display: inline-block;" />)_</sup><br><a href="https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos" style="text-decoration: none;"><small>_Release Notes_</small></a> <sub>_(Does Not Contain MAU)_</sub><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Windows App', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Windows App', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.rdc.macos` | <a href="{get_standalone_package_detail(packages, 'Windows App', 'app_only_update_download')}"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> |
| **Visual Studio Code Standalone Installer**<br><a href="https://code.visualstudio.com/updates/" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Visual', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Visual', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Visual', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.VSCode` | <a href="https://go.microsoft.com/fwlink/?linkid=2156837"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="80"></a>|
| **AutoUpdate Standalone Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-history-microsoft-autoupdate" style="text-decoration: none;"><small>_Release Notes_</small></a><br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'MAU', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'MAU', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'MAU', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.autoupdate` | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="80"></a>|
| **Licensing Helper Tool Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.licensinghelper` | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="80"></a>|
| **Quick Assist Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Quick Assist', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Quick Assist', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Quick Assist', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.quickassist` | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="80"></a>|
| **Remote Help Installer**<br><br>_**Last Update:** `{get_standalone_package_detail(packages, 'Remote Help', 'last_updated')}`_<br> | **Version:**<br>`{get_standalone_package_detail(packages, 'Remote Help', 'short_version')}`<br><br>**Min OS:**<br>`{get_standalone_package_detail(packages, 'Remote Help', 'min_os')}`<br><br>**CFBundle ID:**<br>`com.microsoft.remotehelp` | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'full_update_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="80"></a>|

### SHA256 Information Table

| **Product Package** | **Download** | **SHA256** |
|----------------------|-----------------|------------|
| **Microsoft Office Suite** | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'full_update_sha256')}` |
| **Microsoft BusinessPro Suite** | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'full_update_sha256')}` |
| **Word Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Word', 'full_update_sha256')}` |
| **Word App Only** | <a href="{get_standalone_package_detail(packages, 'Word', 'app_only_update_download')}"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Word', 'app_update_sha256')}` |
| **Excel Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Excel', 'full_update_sha256')}` |
| **Excel App Only** | <a href="{get_standalone_package_detail(packages, 'Excel', 'app_only_update_download')}"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Excel', 'app_update_sha256')}` |
| **PowerPoint Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'PowerPoint', 'full_update_sha256')}` |
| **PowerPoint App Only** | <a href="{get_standalone_package_detail(packages, 'PowerPoint', 'app_only_update_download')}"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'PowerPoint', 'app_update_sha256')}` |
| **Outlook Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Outlook', 'full_update_sha256')}` |
| **Outlook App Only** | <a href="{get_standalone_package_detail(packages, 'Outlook', 'app_only_update_download')}"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Outlook', 'app_update_sha256')}` |
| **OneNote Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'OneNote', 'full_update_sha256')}` |
| **OneNote App Only** | <a href="{get_standalone_package_detail(packages, 'OneNote', 'app_only_update_download')}"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'OneNote', 'app_update_sha256')}` |
| **OneDrive** | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive_512x512x32.png" alt="Download Image" width="80"></a> | `{get_onedrive_package_detail(packages["onedrive"], "Production Ring", 'full_update_sha256')}` |
| **Skype for Business** | <a href="{get_standalone_package_detail(packages, 'Skype', 'app_only_update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Skype', 'full_update_sha256')}` |
| **Teams** | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/teams_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Teams', 'full_update_sha256')}` |
| **Intune Company Portal Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Intune', 'full_update_sha256')}` |
| **Intune Company Portal App Only** | <a href="{get_standalone_package_detail(packages, 'Intune', 'app_only_update_download')}"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Intune', 'app_update_sha256')}` |
| **Edge** | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Edge', 'full_update_sha256')}` |
| **Defender for Endpoint** | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'full_update_sha256')}` |
| **Defender for Consumers** | <a href="https://go.microsoft.com/fwlink/?linkid=2247001"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender For Consumers', 'full_update_sha256')}` |
| **Defender SHIM** | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'app_only_update_download')}"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Defender Shim', 'full_update_sha256')}` |
| **Windows App Standalone** | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Windows App', 'full_update_sha256')}` |
| **Windows App Only** | <a href="{get_standalone_package_detail(packages, 'Windows App', 'app_only_update_download')}"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Windows App', 'app_update_sha256')}` |
| **Visual Studio Code** | <a href="https://go.microsoft.com/fwlink/?linkid=2156837"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Visual', 'full_update_sha256')}` |
| **AutoUpdate** | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'MAU', 'full_update_sha256')}` |
| **Licensing Helper Tool** | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'full_update_sha256')}` |
| **Quick Assist** | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Quick Assist', 'full_update_sha256')}` |
| **Remote Help** | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'full_update_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="80"></a> | `{get_standalone_package_detail(packages, 'Remote Help', 'full_update_sha256')}` |

<sup>_**For items without specific release notes, please refer to the release notes for the entire suite.**_</sup> <br>

<sup>_<img src=".github/images/sha-256.png" alt="Download Image" width="15">[**How to Get the SHA256 Guide**](/guides/How_To_SHA256.md)<img src=".github/images/sha-256.png" alt="Download Image" width="15">_</sup>

| **Last Supported MacOS** | **File Name** | **Version** | **Download** |
|---------------------------|----------------|-------------|--------------|
| macOS 12.7.6 Monterey<br><img src=".github/images/MacOS_Monterey_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.88` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.88.24081116_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 12.7.6 Monterey<br><img src=".github/images/MacOS_Monterey_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.88` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.88.24081116_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 11.7.10 Big Sur<br><img src=".github/images/MacOS_BigSur_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.77` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.77.23091003_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 11.7.10 Big Sur<br><img src=".github/images/MacOS_BigSur_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.77` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_365_and_Office_16.77.23091003_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 10.15.7 Catalina<br><img src=".github/images/MacOS_Catalina_logo.png" alt="macOS Icon" width="60"> | Microsoft Office Suite Installer | `16.66` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_Office_16.66.22100900_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| macOS 10.15.7 Catalina<br><img src=".github/images/MacOS_Catalina_logo.png" alt="macOS Icon" width="60"> | Microsoft BusinessPro Suite Installer| `16.66` | <a href="https://officecdn.microsoft.com/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/Microsoft_Office_16.66.22100900_BusinessPro_Installer.pkg"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |


|      Update History                   |          Microsoft Update Channels               |
|-------------------------|-------------------------|
| <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"> [Microsoft 365/2021/2024](https://learn.microsoft.com/en-us/officeupdates/update-history-office-for-mac) | <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20">  [Microsoft 365 Apps](https://learn.microsoft.com/en-us/microsoft-365-apps/updates/overview-update-channels) |

{macos_table}

{ios_table}

## 🛠️ Microsoft Office Repair Tools & Scripts 🛠️

This section has been moved to the [MOFA website](https://mofa.cocolabs.dev/macos_tools/microsoft_office_repair_tools.html), where you'll find a **comprehensive list of Microsoft Office repair tools** designed to help troubleshoot and resolve common issues on macOS.  

For additional community scripts, visit: [Community Scripts](https://mofa.cocolabs.dev/macos_tools/community_scripts.html).

## **Microsoft Office Preference Keys**

PLIST (Property List) files are used by macOS to store settings and preferences for apps, services, and system configurations, allowing Mac admins to:

- **Customize deployments**
- **Enforce policies**
- **Manage application behavior efficiently**

For a detailed guide on how to create and manage PLIST files, refer to the [How to Plist Guide](/guides/How_To_plist.md).

### **Recommended Resources:**

#### **<img src=".github/images/MAF_Badge_4c.png" alt="Download Image" width="30"> Mac Admin Community-Driven Preferences List (Highly Recommended!)**:
- [View Google Doc](https://docs.google.com/spreadsheets/d/1ESX5td0y0OP3jdzZ-C2SItm-TUi-iA_bcHCBvaoCumw/edit?gid=0#gid=0)

#### **<img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"> Official Microsoft Documentation:**

- [General PLIST Preferences](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deploy-preferences-for-office-for-mac)
- [App-Specific Preferences](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/set-preference-per-app)
- [Outlook Preferences](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/preferences-outlook)
- [Office Suite Preferences](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/preferences-office)

## **Contributing and Providing Feedback**

We warmly welcome your contributions and feedback to **macadmins_msft**! Here’s how you can get involved:

### 📋 **Report Issues**
Have a bug to report or a feature to request? Submit an issue on our [GitHub Issues page](https://github.com/cocopuff2u/macadmins_msft/issues).

### 💬 **Join the Discussion**
Connect and collaborate in the [GitHub Discussions](https://github.com/cocopuff2u/macadmins_msft/discussions) or the [Mac Admins Slack Channel](https://macadmins.slack.com/).
- **Reach Out Directly:** Contact me on Slack at `cocopuff2u` for direct collaboration or questions.
- **New to Slack?** [Sign up here](https://join.slack.com/t/macadmins/shared_invite/zt-2tq3md5zr-jDtuUFHAFa8CIBwPhpFfFQ).
- **Existing User?** [Sign in here](https://macadmins.slack.com/).
- **Explore Slack Channels:**
    - `#microsoft-office`
    - `#microsoft-autoupdate`
    - `#microsoft-intune`
    - `#microsoft-windows-app`
    - `#microsoft-office-365`
    - `#microsoft-teams`

### ✉️ **Contact via Email**
For inquiries, reach out directly at [cocopuff2u@yahoo.com](mailto:cocopuff2u@yahoo.com).

### 🛠️ **Contribute Directly**
Fork the repository, make your changes, and submit a pull request—every contribution counts!

### 💡 **Share Your Feedback**
Help us improve! Share your ideas and suggestions in the [GitHub Discussions](https://github.com/cocopuff2u/macadmins_msft/discussions) or via email.

### 🌟 **Support the Project**
Your contributions directly support the costs of securing a domain name for the upcoming site, with the remainder donated to the Mac Admins community. This project isn’t about profit—it's about giving back to the community and covering minor expenses to make this resource more accessible.  

If you’re feeling extra generous, leave a note to let me know your support is for my coffee fund—it’s always appreciated! Check the button below to support MOFA:

<a href="https://www.buymeacoffee.com/cocopuff2u"><img src="https://img.buymeacoffee.com/button-api/?text=Support This Project&emoji=💻&slug=cocopuff2u&button_colour=5F7FFF&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00" /></a>

## **Helpful Links**

Below are a list of helpful links.
- **Microsoft Versioning Shenanigans**: [View Link](https://macmule.com/2018/09/24/microsoft-office-for-mac-changes-versioning-shenanigans/)
- **Microsoft Deployment Options**: [View Link](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deployment-options-for-office-for-mac)
- **Microsoft Deploy From App Store**: [View Link](https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deploy-mac-app-store)
- **JAMF Technical Paper: Managing Microsoft Office**: [View Link](https://learn.jamf.com/en-US/bundle/technical-paper-microsoft-office-current/page/User_Experience_Configuration.html)

## **Trademarks**

- **Microsoft 365, Office 365, Excel, PowerPoint, Outlook, OneDrive, OneNote, Teams** are trademarks of Microsoft Corporation.
- **Mac** and **macOS** are trademarks of Apple Inc.
- Other names and brands may be claimed as the property of their respective owners.
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
    readme_file_path = "README.md"

    # Parse the XML and generate content
    global_last_updated, packages = parse_latest_xml(xml_file_path)
    ios_last_updated, ios_packages = parse_appstore_xml(ios_appstore_xml_path)
    macos_last_updated, macos_packages = parse_appstore_xml(macos_appstore_xml_path)
    
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
