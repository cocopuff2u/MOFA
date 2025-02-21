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
            "min_os": package.find("min_os").text.strip(),
            "update_download": package.find("update_download").text.strip(),
            "latest_download": package.find("latest_download").text.strip(),
            "sha256": package.find("sha256").text.strip(),
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
        table_content += f"| {application_name} | `{version}` | {bundle_id} | <img src=\"{icon_image}\" alt=\"{application_name}\" width=\"40\"> |\n"

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
        table_content += f"| {application_name} | `{version}` | {bundle_id} | <img src=\"{icon_image}\" alt=\"{application_name}\" width=\"40\"> |\n"

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

### [mofa.cocolabs.dev](https://mofa.cocolabs.dev)

</div>

## <img src=".github/images/Microsoft_Logo_512px.png" alt="Download Image" width="20"></a> Microsoft Standalone Packages

<sup>All links below direct to Microsoft's official Content Delivery Network (CDN).</sup>
<sup>The links provided will always download the latest version offered by Microsoft. However, the version information listed below reflects the version available at the time of this update.</sup>

<sup>_Last Updated: <code style="color : mediumseagreen">{global_last_updated}</code> [**_Raw XML_**](latest_raw_files/macos_standalone_latest.xml) [**_Raw YAML_**](latest_raw_files/macos_standalone_latest.yaml) [**_Raw JSON_**](latest_raw_files/macos_standalone_latest.json) (Automatically Updated every 1 hour)_</sup>

| **Product Package** | **CFBundle Version** | **CFBundle Identifier** | **Download** |
|----------------------|----------------------|--------------------------|--------------|
| **Microsoft** <sup>365/2021/2024</sup> **Office Suite Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac" style="text-decoration: none;"><small>_Release Notes_</small></a><br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, and MAU)_</sub> | `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'short_version')}` | com.microsoft.office | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Microsoft** <sup>365/2021/2024</sup> **BusinessPro Suite Installer**<br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Defender Shim, and MAU)_</sub> | `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'short_version')}` | com.microsoft.office | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="80"></a> |
| **Word** <sup>365/2021/2024</sup> **</sup> Standalone Installer** | `{get_standalone_package_detail(packages, 'Word', 'short_version')}` | com.microsoft.word | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'Excel', 'short_version')}` | com.microsoft.excel | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}` | com.microsoft.powerpoint | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'Outlook', 'short_version')}` | com.microsoft.outlook | <a href="https://go.microsoft.com/fwlink/?linkid=2228621"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a>|
| **OneNote** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'OneNote', 'short_version')}` | com.microsoft.onenote.mac | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> |
| **OneDrive Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/onedrive-release-notes-845dcf18-f921-435e-bf28-4e24b95e5fc0#OSVersion=Mac" style="text-decoration: none;"><small>_Release Notes_</small></a> | `{get_standalone_package_detail(packages, 'OneDrive', 'short_version')}` | com.microsoft.OneDrive | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive_512x512x32.png" alt="Download Image" width="80"></a> |
| **Skype for Business Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/follow-the-latest-updates-in-skype-for-business-cece9f93-add1-4d93-9a38-56cc598e5781?ui=en-us&rs=en-us&ad=us" style="text-decoration: none;"><small>_Release Notes_</small></a>  | `{get_standalone_package_detail(packages, 'Skype', 'short_version')}` | com.microsoft.SkypeForBusiness | <a href="{get_standalone_package_detail(packages, 'Skype', 'update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="80"></a> |
| **Teams Standalone Installer**<br><a href="https://support.microsoft.com/en-us/office/what-s-new-in-microsoft-teams-d7092a6d-c896-424c-b362-a472d5f105de" style="text-decoration: none;"><small>_Release Notes_</small></a>  | `{get_standalone_package_detail(packages, 'Teams', 'short_version')}` | com.microsoft.teams2 | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/teams_512x512x32.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal Standalone Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a> | `{get_standalone_package_detail(packages, 'Intune', 'short_version')}` | com.microsoft.CompanyPortalMac | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **Edge Standalone Installer** <sup>_(Stable Channel)_</sup><br><a href="https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel" style="text-decoration: none;"><small>_Release Notes_</small></a>| `{get_standalone_package_detail(packages, 'Edge', 'short_version')}` | com.microsoft.edgemac | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="80"></a>|
| **Defender for Endpoint Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a> | `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'short_version')}` | com.microsoft.wdav | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Defender for Consumers Installer**<br><a href="https://learn.microsoft.com/microsoft-365/security/defender-endpoint/mac-whatsnew" style="text-decoration: none;"><small>_Release Notes_</small></a> | `{get_standalone_package_detail(packages, 'Defender For Consumers', 'short_version')}` | com.microsoft.wdav | <a href="https://go.microsoft.com/fwlink/?linkid=2247001"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Defender SHIM Installer** | `{get_standalone_package_detail(packages, 'Defender Shim', 'short_version')}` | com.microsoft.wdav.shim | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'update_download')}"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="80"></a> |
| **Windows App Standalone Installer** </a><sup>_(Remote Desktop <img src=".github/images/microsoft-remote-desktop-logo.png" alt="Remote Desktop" width="15"></a>)_</sup><br><a href="https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos" style="text-decoration: none;"><small>_Release Notes_</small> | `{get_standalone_package_detail(packages, 'Windows App', 'short_version')}` | com.microsoft.rdc.macos | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="80"></a> |
| **Visual Studio Code Standalone Installer**<br><a href="https://code.visualstudio.com/updates/" style="text-decoration: none;"><small>_Release Notes_</small></a>  | `{get_standalone_package_detail(packages, 'Visual', 'short_version')}` | com.microsoft.VSCode | <a href="https://go.microsoft.com/fwlink/?linkid=2156837"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="80"></a>|
| **AutoUpdate Standalone Installer**<br><a href="https://learn.microsoft.com/en-us/officeupdates/release-history-microsoft-autoupdate" style="text-decoration: none;"><small>_Release Notes_</small></a>  | `{get_standalone_package_detail(packages, 'MAU', 'short_version')}` | com.microsoft.autoupdate | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="80"></a>|
| **Licensing Helper Tool Installer** | `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'short_version')}` | N/A | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'latest_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="80"></a>|
| **Quick Assist Installer** | `{get_standalone_package_detail(packages, 'Quick Assist', 'short_version')}` | com.microsoft.quickassist | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'latest_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="80"></a>|
| **Remote Help Installer** | `{get_standalone_package_detail(packages, 'Remote Help', 'short_version')}` | com.microsoft.remotehelp | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'latest_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="80"></a>|

<sup>_**For items without specific release notes, please refer to the release notes for the entire suite.**_</sup> <br>

<sup>_**All apps include MAU with installation, except for Skype for Business, OneDrive, Defender SHIM, Licensing Helper Tool, Quick Assist, and Remote Help.**_</sup>

| **Product Package** | **Link** | **<img src=".github/images/sha-256.png" alt="Download Image" width="20">SHA256 Hash<img src=".github/images/sha-256.png" alt="Download Image" width="20">** |
|----------------------|----------|------------------|
| **Microsoft** <sup>365/2021/2024</sup> **and Office Suite Installer**<br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, and MAU)_</sub> | <a href="https://go.microsoft.com/fwlink/?linkid=525133"><img src=".github/images/suite.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Microsoft Office Suite', 'sha256')}` |
| **Microsoft** <sup>365/2021/2024</sup> **BusinessPro Suite Installer**<br><sub>_(Includes Word, Excel, PowerPoint, Outlook, OneNote, OneDrive, Teams, Defender Shim, and MAU)_</sub> | <a href="https://go.microsoft.com/fwlink/?linkid=2009112"><img src=".github/images/suite.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Microsoft BusinessPro Suite', 'sha256')}` |
| **Word** <sup>365/2021/2024</sup> **Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=525134"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Word', 'sha256')}` |
| **Excel** <sup>365/2021/2024</sup> **Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=525135"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Excel', 'sha256')}` |
| **PowerPoint** <sup>365/2021/2024</sup> **Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=525136"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'PowerPoint', 'sha256')}` |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer**| <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Outlook', 'sha256')}` |
| **OneNote** <sup>365/2021/2024</sup> **Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=820886"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'OneNote', 'sha256')}` |
| **OneDrive Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=823060"><img src=".github/images/OneDrive_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'OneDrive', 'sha256')}` |
| **Skype for Business Standalone Installer** | <a href="{get_standalone_package_detail(packages, 'Skype', 'update_download')}"><img src=".github/images/skype_for_business.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Skype', 'sha256')}` |
| **Teams Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=2249065"><img src=".github/images/teams_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Teams', 'sha256')}` |
| **InTune Company Portal Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=853070"><img src=".github/images/companyportal.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Intune', 'sha256')}` |
| **Edge Standalone Installer** <sup>_(Stable Channel)_</sup> | <a href="https://go.microsoft.com/fwlink/?linkid=2093504"><img src=".github/images/edge_app.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Edge', 'sha256')}` |
| **Defender For Endpoint Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=2097502"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Defender For Endpoint', 'sha256')}` |
| **Defender For Consumer Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=2097001"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Defender For Consumers', 'sha256')}` |
| **Defender Shim Installer** | <a href="{get_standalone_package_detail(packages, 'Defender Shim', 'latest_download')}"><img src=".github/images/defender_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Defender Shim', 'sha256')}` |
| **Windows App Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=868963"><img src=".github/images/windowsapp.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Windows App', 'sha256')}` |
| **Visual Studio Code Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=2156837"><img src=".github/images/Code_512x512x32.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Visual', 'sha256')}` |
| **AutoUpdate Standalone Installer** | <a href="https://go.microsoft.com/fwlink/?linkid=830196"><img src=".github/images/autoupdate.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'MAU', 'sha256')}` |
| **Licensing Helper Tool Installer** | <a href="{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'latest_download')}"><img src=".github/images/pkg-icon.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Licensing Helper Tool', 'sha256')}` |
| **Quick Assist Installer** | <a href="{get_standalone_package_detail(packages, 'Quick Assist', 'latest_download')}"><img src=".github/images/quickassist.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Quick Assist', 'sha256')}` |
| **Remote Help Installer** | <a href="{get_standalone_package_detail(packages, 'Remote Help', 'latest_download')}"><img src=".github/images/remotehelp.png" alt="Download Image" width="60"></a> | `{get_standalone_package_detail(packages, 'Remote Help', 'sha256')}` |

<sup>_<img src=".github/images/sha-256.png" alt="Download Image" width="15">[**How to Get the SHA256 Guide**](/guides/How_To_SHA256.md)<img src=".github/images/sha-256.png" alt="Download Image" width="15">_</sup>

| **Special Product Package** | **CFBundle Version** | **MAU Status** | **Download** |
|----------------------|----------------------|--------------------------|--------------|
| **Word** <sup>365/2021/2024</sup> **</sup> Standalone Installer** | `{get_standalone_package_detail(packages, 'Word', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'Word', 'update_download')}"><img src=".github/images/MSWD_512x512x32.png" alt="Download Image" width="80"></a> |
| **Excel** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'Excel', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'Excel', 'update_download')}"><img src=".github/images/XCEL_512x512x32.png" alt="Download Image" width="80"></a> |
| **PowerPoint** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'PowerPoint', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'PowerPoint', 'update_download')}"><img src=".github/images/PPT3_512x512x32.png" alt="Download Image" width="80"></a> |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer**<sup>_(Weekly Channel)_</sup>| `{get_standalone_package_detail(packages, 'Outlook', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'Outlook', 'update_download')}"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a>|
| **OneNote** <sup>365/2021/2024</sup> **Standalone Installer** | `{get_standalone_package_detail(packages, 'OneNote', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'OneNote', 'update_download')}"><img src=".github/images/OneNote_512x512x32.png" alt="Download Image" width="80"></a> |
| **InTune Company Portal Standalone Installer**<br><a href="https://aka.ms/intuneupdates" style="text-decoration: none;"><small>_Release Notes_</small></a> | `{get_standalone_package_detail(packages, 'Intune', 'short_version')}` | No MAU | <a href="{get_standalone_package_detail(packages, 'Intune', 'update_download')}"><img src=".github/images/companyportal.png" alt="Download Image" width="80"></a> |
| **Outlook** <sup>365/2021/2024</sup> **Standalone Installer**<sup>_(Monthly Channel)_</sup>| `N/A - Check Release Notes` | Contains MAU | <a href="https://go.microsoft.com/fwlink/?linkid=525137"><img src=".github/images/Outlook_512x512x32.png" alt="Download Image" width="80"></a>|

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

## **<img src=".github/images/repair.png" alt="Repair Image" width="20"></a> Microsoft Office Repair Tools <img src=".github/images/repair.png" alt="Repair Image" width="20"></a>**

### **<img src="/.github/images/Office_Reset_512x512.png" alt="Office Reset Logo" width="25"> [Office-Reset.com](https://office-reset.com/macadmins/)<img src="/.github/images/Office_Reset_512x512.png" alt="Office Reset Logo" width="25">**
- A free tool to fix issues with Microsoft Office apps on macOS (e.g., crashes, performance problems). It offers various packages for resetting settings and clearing cache.
<br>**_<img src=".github/images/warning.png" alt="Warning Logo" width="25"> No Longer Updated/Maintained <img src=".github/images/warning.png" alt="Warning Logo" width="25">_**

### **<img src=".github/images/pkg-icon.png" alt="Pkg Logo" width="25"> [Office-Reset Packages/Scripts](/office_reset_tools/office_reset_archived/)<img src=".github/images/pkg-icon.png" alt="Pkg Logo" width="25">**
- Archived copies of the original Office-Reset packages in a pkg and script format, now saved to this repository.
<br>**_<img src=".github/images/warning.png" alt="Warning Logo" width="25"> No Longer Updated/Maintained <img src=".github/images/warning.png" alt="Warning Logo" width="25">_**

### **<img src=".github/images/repair.png" alt="Repair Image" width="20"></a> [MOFA Maintained Packages/Scripts](/office_reset_tools/mofa_community_maintained/) <img src=".github/images/repair.png" alt="Repair Image" width="20"></a>**
- **MOFA** community-maintained versions, based on and updated from the original Office-Reset.com packages. Fork, update, and improve these scripts for continued community use.
<br>**_<img src=".github/images/community.png" alt="Community Logo" width="25"> Needs More Community Contributions <img src=".github/images/community.png" alt="Community Logo" width="25">_**

## **<img src=".github/images/script.png" alt="Script Image" width="20"> Microsoft Scripts <img src=".github/images/script.png" alt="Script Image" width="20">**

These scripts automate the process of downloading, installing, updating, and managing Microsoft products.

- **Download & Install Microsoft Products**: [View Script](https://gist.github.com/talkingmoose/b6637160b65b751824943ede022daa17) by [TalkingMoose](https://github.com/talkingmoose)
  This script automates the downloading and installation of the latest Microsoft products using direct links and includes optional SHA256 verification for added security.

- **Install Office 365 Pro**: [View Script](https://github.com/microsoft/shell-intune-samples/blob/master/macOS/Apps/Office%20for%20Mac/installOffice365Pro.sh) by [Microsoft](https://github.com/microsoft)
  This script automates the downloading and installation of the Office 365 Pro.

- **Installomator**: [View Script](https://github.com/Installomator/Installomator) by [Installomator](https://github.com/Installomator)
  A powerful tool for automating the deployment of Microsoft Office products on macOS, simplifying downloading, installation, and updates.

- **Various Tools**: [View Scripts](https://github.com/pbowden-msft?tab=repositories) by [pbowden-msft](https://github.com/pbowden-msft)
  A collection of tools for repairing, setting up, and automating Microsoft Office products.

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

 <a href="https://trackgit.com">
<img src="https://us-central1-trackgit-analytics.cloudfunctions.net/token/ping/m4kk2865o4y6sixk54sm" alt="trackgit-views" />
</a>
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

if __name__ == "__main__":
    # Define file paths
    xml_file_path = "latest_raw_files/macos_standalone_latest.xml"  # Update this path if the file is located elsewhere
    ios_appstore_xml_path = "latest_raw_files/ios_appstore_latest.xml"
    macos_appstore_xml_path = "latest_raw_files/macos_appstore_latest.xml"
    readme_file_path = "README.md"

    # Parse the XML and generate content
    global_last_updated, packages = parse_latest_xml(xml_file_path)
    ios_last_updated, ios_packages = parse_appstore_xml(ios_appstore_xml_path)
    macos_last_updated, macos_packages = parse_appstore_xml(macos_appstore_xml_path)

    # Merge packages
    packages.update(ios_packages)
    packages.update(macos_packages)

    readme_content = generate_readme_content(global_last_updated, packages, ios_packages, macos_packages)

    # Overwrite the README file
    overwrite_readme(readme_file_path, readme_content)
