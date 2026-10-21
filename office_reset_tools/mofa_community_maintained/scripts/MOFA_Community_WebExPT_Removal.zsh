#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_WebExPT_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the WebExPT application
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Fixed $HOME variable shadowing (renamed to $UserHome); removed unused autoload;
#          updated conditionals to zsh-native [[ ]]; removed invalid launchctl stop (plist path
#          instead of job label); replaced launchctl unload with bootout using correct GUI domain;
#          added LaunchAgent plist deletion after unload; added cfprefsd flush; added existence
#          check for native uninstaller; added pkill for running processes; fixed header filename.
#
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_WebExPT"

APP_NAME="WebEx Productivity Tools"
UNINSTALLER="/Applications/WebEx Productivity Tools/Uninstall/Contents/MacOS/Uninstall"

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
    # Prefer NFSHomeDirectory from dscl; fall back to /Users/<username>.
    # No eval: the username is never passed through the shell parser.
    UserHome=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | sed -n 's/^NFSHomeDirectory: //p')
    if [[ -z "$UserHome" ]]; then
        UserHome="/Users/$1"
    fi
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $UserHome"

echo "Office-Reset: Stopping ${APP_NAME} processes"
/usr/bin/pkill -9 'WebEx Productivity Tools' 2>/dev/null; true
/usr/bin/pkill -9 'webexmta'                 2>/dev/null; true
/usr/bin/pkill -9 'pluginagent'              2>/dev/null; true

# Run the native uninstaller if present. The uninstaller lives inside the app bundle,
# so it must be executed before the bundle itself is removed below.
if [[ -x "$UNINSTALLER" ]]; then
    echo "Office-Reset: Running native uninstall routine for ${APP_NAME}"
    "$UNINSTALLER"
else
    echo "Office-Reset: Native uninstaller not found at $UNINSTALLER — skipping"
fi

# Unload the WebEx LaunchAgent from the logged-in user's GUI session.
# launchctl stop takes a job *label*, not a plist path — using it with a path is a no-op.
# launchctl bootout with the gui/<uid> domain correctly targets the user session.
echo "Office-Reset: Unloading ${APP_NAME} LaunchAgent"
LoggedInUID=$(id -u "$LoggedInUser")
/bin/launchctl bootout gui/"$LoggedInUID" /Library/LaunchAgents/com.webex.pluginagent.plist 2>/dev/null; true

# Flush cfprefsd cache before removing preference plists.
# Without this, cfprefsd may recreate plists from its in-memory cache after deletion.
/usr/bin/killall cfprefsd 2>/dev/null; true

echo "Office-Reset: Removing ${APP_NAME} LaunchAgent configuration"
/bin/rm -f "/Library/LaunchAgents/com.webex.pluginagent.plist"

echo "Office-Reset: Removing ${APP_NAME} preferences"
/bin/rm -f "$UserHome/Library/Preferences/com.cisco.webex.pluginservice.plist"
/bin/rm -f "$UserHome/Library/Preferences/com.cisco.webex.webexmta.plist"
/bin/rm -f "$UserHome/Library/Preferences/com.cisco.webex.meetings.plist"

echo "Office-Reset: Removing ${APP_NAME} user data"
/bin/rm -rf "$UserHome/Library/Application Support/Cisco/Webex Plugin"
/bin/rm -rf "$UserHome/Library/Application Support/Cisco/Webex Meetings"
/bin/rm -rf "$UserHome/Library/Caches/com.cisco.webex.pluginservice"
/bin/rm -rf "$UserHome/Library/Caches/com.cisco.webex.webexmta"
/bin/rm -rf "$UserHome/Library/Group Containers/group.com.cisco.webex.meetings"
/bin/rm -rf "$UserHome/Library/Logs/PT"
/bin/rm -rf "$UserHome/Library/Logs/webexmta"

echo "Office-Reset: Removing ${APP_NAME} system-level files"
/bin/rm -rf "/Library/Application Support/Microsoft/WebExPlugin"
/bin/rm -rf "/Library/ScriptingAdditions/WebexScriptAddition.osax"
/bin/rm -rf "/Users/Shared/WebExPlugin"

# Remove the app bundle in case the native uninstaller left it behind or was absent.
/bin/rm -rf "/Applications/WebEx Productivity Tools"

echo "Office-Reset: Removing package receipts"
/usr/sbin/pkgutil --forget olp.mac.webex.com

echo "Office-Reset: ${APP_NAME} removal complete for $LoggedInUser"
exit 0
