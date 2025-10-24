import xml.etree.ElementTree as ET
from datetime import datetime
import os

# Get the root directory of the project (assuming the script is inside a subfolder like '/update_readme_scripts/')
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(project_root)  # go up from .github to repo root

# Define the correct paths based on the project root
latest_xml_path = os.path.join(repo_root, 'latest_raw_files', 'macos_standalone_latest.xml')
# Replace single-feed path with a directory + per-package filenames
FEEDS_DIR = os.path.join(repo_root, 'latest_raw_files', 'macos_standalone_rss')
FEED_BASE_URL = "https://mofa.cocolabs.dev/rss_feeds"

# Print the paths to verify if they are correct
print(f"Latest XML Path: {latest_xml_path}")
print(f"RSS Feeds Directory: {FEEDS_DIR}")

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# Create the latest.xml file if it doesn't exist
if not os.path.exists(latest_xml_path):
    root = ET.Element('packages')
    tree = ET.ElementTree(root)
    indent(root)
    tree.write(latest_xml_path, encoding='UTF-8', xml_declaration=True)

# Constants for URLs
SITE_URL = "https://mofa.cocolabs.dev/"

# Per-package hard values (add/remove packages here)
PACKAGES = [
    {
        "name": "Microsoft Office Suite",
        "feed_filename": "office_suite_rss.xml",
        "channel_title": "MOFA - Office Suite RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Office Suite RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft Office Suite Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "MAU",
        "feed_filename": "mau_rss.xml",
        "channel_title": "MOFA - MAU RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - MAU RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-history-microsoft-autoupdate",
        "item_title": "New Microsoft AutoUpdate Released",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Word",
        "feed_filename": "word_rss.xml",
        "channel_title": "MOFA - Word RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Word RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft Word Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Excel",
        "feed_filename": "excel_rss.xml",
        "channel_title": "MOFA - Excel RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Excel RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft Excel Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "PowerPoint",
        "feed_filename": "powerpoint_rss.xml",
        "channel_title": "MOFA - PowerPoint RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - PowerPoint RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft PowerPoint Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Outlook",
        "feed_filename": "outlook_rss.xml",
        "channel_title": "MOFA - Outlook RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Outlook RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft Outlook Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "OneNote",
        "feed_filename": "onenote_rss.xml",
        "channel_title": "MOFA - OneNote RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - OneNote RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/officeupdates/release-notes-office-for-mac",
        "item_title": "New Microsoft OneNote Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Teams",
        "feed_filename": "teams_rss.xml",
        "channel_title": "MOFA - Teams RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Teams RSS Feed",
        "release_notes_url": "https://support.microsoft.com/en-us/office/what-s-new-in-microsoft-teams-d7092a6d-c896-424c-b362-a472d5f105de",
        "item_title": "New Microsoft Teams Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Intune",
        "feed_filename": "company_portal_rss.xml",
        "channel_title": "MOFA - Company Portal RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Company Portal RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/intune/intune-service/fundamentals/whats-new",
        "item_title": "New Microsoft Company Portal Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Defender For Endpoint",
        "feed_filename": "defender_for_endpoint_rss.xml",
        "channel_title": "MOFA - Defender For Endpoint RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Defender For Endpoint RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/defender-endpoint/mac-whatsnew",
        "item_title": "New Microsoft Defender For Endpoint Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    },
    {
        "name": "Windows App",
        "feed_filename": "windows_app_rss.xml",
        "channel_title": "MOFA - Windows App RSS Feed",
        "channel_description": "Microsoft Office Feed for Apple - Windows App RSS Feed",
        "release_notes_url": "https://learn.microsoft.com/en-us/windows-app/whats-new?tabs=macos",
        "item_title": "New Microsoft Windows App Release",
        "image_url": "https://mofa.cocolabs.dev/images/logo_Mofa_NoBackground.png",
    }
]

# Helper: get all textual content from an element (text + children text/tails)
def _get_all_text(el: ET.Element) -> str:
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if child.text:
            parts.append(child.text)
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)

# Build the <description> as escaped HTML text (no child elements, no CDATA)
def _set_description_with_link(desc_el: ET.Element, version: str, release_notes_url: str) -> None:
    desc_el.clear()
    desc_el.text = (
        "Microsoft AutoUpdate"
        "<br>"
        f"Version: {version}"
        "<br>"
        f"Release Notes: <a href=\"{release_notes_url}\">Release Notes</a>"
    )

# Parse the latest.xml file
latest_tree = ET.parse(latest_xml_path)
latest_root = latest_tree.getroot()

# Register atom namespace for proper find/create
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}

def _ensure_feed_exists(feed_path: str) -> None:
    if not os.path.exists(feed_path) or os.path.getsize(feed_path) == 0:
        rss = ET.Element('rss', {'version': '2.0', 'xmlns:atom': 'http://www.w3.org/2005/Atom'})
        ET.SubElement(rss, 'channel')
        tree = ET.ElementTree(rss)
        indent(rss)
        os.makedirs(os.path.dirname(feed_path), exist_ok=True)
        tree.write(feed_path, encoding='UTF-8', xml_declaration=True)

def _find_package_node(root: ET.Element, package_name: str):
    for package in root.findall('package'):
        name_el = package.find('name')
        if name_el is not None and name_el.text == package_name:
            return package
    return None

def _update_rss_for_package(pkg_conf: dict, pkg_node: ET.Element) -> None:
    short_version = (pkg_node.find('short_version').text or "").strip()
    update_download = (pkg_node.find('app_only_update_download').text or "").strip()
    last_updated = (pkg_node.find('last_updated').text or "").strip()

    # Compute per-package feed paths/urls
    feed_filename = pkg_conf['feed_filename']
    feed_path = os.path.join(FEEDS_DIR, feed_filename)
    feed_url = f"{FEED_BASE_URL}/{feed_filename}"

    # Prepare dates
    last_build_date_text = datetime.strptime(last_updated, "%B %d, %Y").strftime("%a, %d %b %Y 00:00:00 +0000")

    # Ensure feed file exists
    _ensure_feed_exists(feed_path)

    # Parse the RSS feed
    rss_tree = ET.parse(feed_path)
    rss_root = rss_tree.getroot()
    channel = rss_root.find('channel')

    # Initialize channel-level elements if they do not exist
    title = channel.find('title')
    link = channel.find('link')
    description = channel.find('description')
    docs = channel.find('docs')

    if title is None:
        title = ET.SubElement(channel, 'title')
    title.text = pkg_conf['channel_title']

    if link is None:
        link = ET.SubElement(channel, 'link')
    # Always ensure canonical channel link points to the site (not the feed URL)
    link.text = SITE_URL

    if description is None:
        description = ET.SubElement(channel, 'description')
    description.text = pkg_conf['channel_description']

    if docs is None:
        docs = ET.SubElement(channel, 'docs')
    docs.text = "http://www.rssboard.org/rss-specification"

    # Add/update atom:link rel="self" for the feed URL
    atom_link = channel.find('atom:link', ATOM_NS)
    if atom_link is None:
        atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {
            'href': feed_url,
            'rel': 'self',
            'type': 'application/rss+xml'
        })
    else:
        atom_link.set('href', feed_url)
        atom_link.set('rel', 'self')
        atom_link.set('type', 'application/rss+xml')

    # Add/ensure language, ttl, and lastBuildDate
    language = channel.find('language')
    if language is None:
        language = ET.SubElement(channel, 'language')
    language.text = 'en-US'

    ttl = channel.find('ttl')
    if ttl is None:
        ttl = ET.SubElement(channel, 'ttl')
    ttl.text = '60'

    last_build_date = channel.find('lastBuildDate')
    if last_build_date is None:
        last_build_date = ET.SubElement(channel, 'lastBuildDate')
    last_build_date.text = last_build_date_text

    # Add the <image> element above the <item> elements
    image = channel.find('image')
    if image is None:
        image = ET.Element('image')
        url = ET.SubElement(image, 'url')
        url.text = pkg_conf['image_url']
        img_title = ET.SubElement(image, 'title')
        img_title.text = pkg_conf['channel_title']
        img_link = ET.SubElement(image, 'link')
        img_link.text = SITE_URL
        first_item_index = next((i for i, elem in enumerate(channel) if elem.tag == 'item'), len(channel))
        channel.insert(first_item_index, image)
    else:
        # Ensure image link points to the site URL
        img_link = image.find('link')
        if img_link is None:
            img_link = ET.SubElement(image, 'link')
        img_link.text = SITE_URL

    # Remove duplicate non-atom channel <link> elements (keep the first one as canonical)
    links = channel.findall('link')
    if links:
        links[0].text = SITE_URL
        for extra in links[1:]:
            channel.remove(extra)
    else:
        ET.SubElement(channel, 'link').text = SITE_URL

    # Check if the package version already exists in the RSS feed
    existing_version = False
    for item in channel.findall('item'):
        title_el = item.find('title')
        desc_el = item.find('description')
        if not (title_el is None or desc_el is None):
            desc_text = _get_all_text(desc_el)
            if (short_version in (title_el.text or "")) or (short_version in desc_text):
                _set_description_with_link(desc_el, short_version, pkg_conf['release_notes_url'])
                existing_version = True
                print(f"{pkg_conf['name']}: version already in RSS feed")
                break

    # If the version is not already in the feed, add it
    if not existing_version:
        new_item = ET.Element('item')
        title_el = ET.SubElement(new_item, 'title')
        title_el.text = pkg_conf['item_title']
        link_el = ET.SubElement(new_item, 'link')
        link_el.text = update_download
        desc_el = ET.SubElement(new_item, 'description')
        _set_description_with_link(desc_el, short_version, pkg_conf['release_notes_url'])
        pubDate = ET.SubElement(new_item, 'pubDate')
        pubDate.text = last_build_date_text
        guid = ET.SubElement(new_item, 'guid')
        guid.text = update_download
        guid.set('isPermaLink', 'false')

        # Insert the new item into the RSS feed
        first_item_index = next((i for i, elem in enumerate(channel) if elem.tag == 'item'), len(channel))
        channel.insert(first_item_index, new_item)
        print(f"{pkg_conf['name']}: RSS feed updated with new version")

    # Always write updates (even if only header normalization happened)
    indent(rss_root)
    rss_tree.write(feed_path, encoding='UTF-8', xml_declaration=True)

# Process each configured package
for pkg in PACKAGES:
    node = _find_package_node(latest_root, pkg['name'])
    if node is None:
        print(f"{pkg['name']}: package not found in latest.xml; skipping.")
        continue
    _update_rss_for_package(pkg, node)