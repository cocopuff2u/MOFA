#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_ZoomPlugin_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the Zoom Plugin for Microsoft Outlook/Office
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - CRITICAL: Replaced entire script body — v1.0.0 was a verbatim copy of the
#          Skype for Business removal script and removed SfB, not Zoom Plugin.
#          Fixed $HOME variable shadowing (renamed to $UserHome); removed unused autoload
#          and unused SCRIPT_FOLDER; updated conditionals to zsh-native [[ ]]; replaced
#          launchctl unload with bootout using correct GUI domain; added cfprefsd flush;
#          added LaunchAgent plist deletion after unload; added pkill before cleanup;
#          removed inapplicable dockutil call (Zoom Plugin has no Dock entry);
#          fixed header Script Name comment.
#
# NOTE: Zoom Plugin paths below reflect the standard ZoomOutlookPlugin installation layout.
# To verify paths on a target machine: pkgutil --files us.zoom.pkg.ZoomOutlookPlugin
#
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_ZoomPlugin"

GetLoggedInUser() {
    local loggedIn
    loggedIn=$(/bin/echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/Name :/&&!/loginwindow/{print $3}')
    if [[ -z "$loggedIn" ]]; then
        echo "$USER"
    else
        echo "$loggedIn"
    fi
}

SetHomeFolder() {
    UserHome=$(dscl . read /Users/"$1" NFSHomeDirectory | cut -d ':' -f2 | cut -d ' ' -f2)
    if [[ -z "$UserHome" ]]; then
        if [[ -d "/Users/$1" ]]; then
            UserHome="/Users/$1"
        else
            UserHome=$(eval echo "~$1")
        fi
    fi
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $UserHome"

echo "Office-Reset: Stopping Zoom Plugin processes"
/usr/bin/pkill -9 'ZoomOutlookPlugin' 2>/dev/null; true
/usr/bin/pkill -9 'ZoomPlugin'        2>/dev/null; true

# Unload the Zoom Plugin LaunchAgent from the logged-in user's GUI session.
# launchctl bootout with gui/<uid> correctly targets the user session when run as root.
echo "Office-Reset: Unloading Zoom Plugin LaunchAgent"
LoggedInUID=$(id -u "$LoggedInUser")
/bin/launchctl bootout gui/"$LoggedInUID" /Library/LaunchAgents/us.zoom.ZoomPlugin.plist 2>/dev/null; true

# Flush cfprefsd cache before removing preference plists.
# Without this, cfprefsd may recreate plists from its in-memory cache after deletion.
/usr/bin/killall cfprefsd 2>/dev/null; true

echo "Office-Reset: Removing Zoom Plugin LaunchAgent configuration"
/bin/rm -f "/Library/LaunchAgents/us.zoom.ZoomPlugin.plist"

echo "Office-Reset: Removing Zoom Plugin preferences"
/bin/rm -f "$UserHome/Library/Preferences/us.zoom.ZoomPlugin.plist"
/bin/rm -f "/Library/Preferences/us.zoom.ZoomPlugin.plist"
/bin/rm -f "/Library/Managed Preferences/us.zoom.ZoomPlugin.plist"

echo "Office-Reset: Removing Zoom Plugin user data"
/bin/rm -rf "$UserHome/Library/Application Support/zoom.us/ZoomPlugin"
/bin/rm -rf "$UserHome/Library/Caches/us.zoom.ZoomPlugin"
/bin/rm -rf "$UserHome/Library/Saved Application State/us.zoom.ZoomOutlookPlugin.savedState"
/bin/rm -f  "$UserHome/Library/Cookies/us.zoom.ZoomOutlookPlugin.binarycookies"

echo "Office-Reset: Removing Zoom Plugin app and system-level files"
/bin/rm -rf "/Applications/ZoomOutlookPlugin.app"
/bin/rm -rf "/Library/Application Support/zoom.us/ZoomPlugin"

echo "Office-Reset: Removing package receipts"
/usr/sbin/pkgutil --forget us.zoom.pkg.ZoomOutlookPlugin
/usr/sbin/pkgutil --forget us.zoom.ZoomPlugin

echo "Office-Reset: Zoom Plugin removal complete for $LoggedInUser"
exit 0
