#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_ZoomPlugin_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the Zoom Plugin for Microsoft Outlook (legacy injection plugin)
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Replaced the entire script body. v1.0.0 was a verbatim copy of the Skype for
#          Business removal script and removed SfB, not the Zoom Plugin. Removal targets
#          below are taken from the payload, postinstall script and Uninstall.app of
#          Zoom's ZoomMacOutlookPlugin.pkg (5.12.0, receipt id ZoomMacOutlookPlugin.pkg).
#          Also: $HOME no longer shadowed (renamed to $UserHome), eval removed from
#          SetHomeFolder, zsh-native [[ ]] conditionals, launchctl bootout in the
#          logged-in user's GUI domain, LaunchAgent plists deleted after unload.
#
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_ZoomPlugin"
SCRIPT_FOLDER=$(/usr/bin/dirname "$0")

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
LoggedInUID=$(id -u "$LoggedInUser" 2>/dev/null)
echo "Office-Reset: Running as: $LoggedInUser (UID: $LoggedInUID); Home Folder: $UserHome"

echo "Office-Reset: Stopping Zoom Plugin processes"
# Match on the full path so an unrelated "PluginLauncher" process is never killed.
/usr/bin/pkill -9 -f '/ZoomOutlookPlugin/PluginLauncher.app/' 2>/dev/null; true
/usr/bin/pkill -9 'zOutlookPluginAgent' 2>/dev/null; true

# The installer places us.zoom.pluginagent.plist in /Library/LaunchAgents and copies it
# into the logged-in user's ~/Library/LaunchAgents. Unload both from the user's GUI
# domain (the script runs as root), then delete them so launchd does not reload them.
echo "Office-Reset: Unloading Zoom Plugin LaunchAgent"
for plist in \
    "/Library/LaunchAgents/us.zoom.pluginagent.plist" \
    "$UserHome/Library/LaunchAgents/us.zoom.pluginagent.plist"; do
    if [[ -f "$plist" ]]; then
        /bin/launchctl bootout gui/"$LoggedInUID" "$plist" 2>/dev/null; true
        /bin/rm -f "$plist"
    fi
done

/usr/bin/killall cfprefsd 2>/dev/null; true

echo "Office-Reset: Removing Zoom Plugin preferences"
/bin/rm -f "$UserHome/Library/Preferences/us.zoom.pluginagent.plist"
/bin/rm -f "$UserHome/Library/Preferences/us.zoom.olpluginlauncher.plist"

echo "Office-Reset: Removing Zoom Plugin files"
# Admin install location (PluginLauncher.app, Uninstall.app)
/bin/rm -rf "/Applications/ZoomOutlookPlugin"
# Non-admin install location
/bin/rm -rf "$UserHome/Library/Application Support/ZoomOutlookPlugin"
# Agent app launched by the LaunchAgent
/bin/rm -rf "/Library/Application Support/ZoomOutlookPlugin"
# Outlook plugin bundles (zOutlookPlugin.bundle / zOutlookPlugin64.bundle)
/bin/rm -rf "/Library/Application Support/Microsoft/ZoomOutlookPlugin"
/bin/rm -rf "/Users/Shared/ZoomOutlookPlugin"
# Scripting addition used to inject into Outlook (current and pre-5.x names)
/bin/rm -rf "/Library/ScriptingAdditions/zOLPluginInjection.osax"
/bin/rm -rf "/Library/ScriptingAdditions/zPluginScriptAddition.osax"
/bin/rm -f  "/Library/Logs/zoomoutlookplugin.log"

echo "Office-Reset: Removing package receipts"
/usr/sbin/pkgutil --forget ZoomMacOutlookPlugin.pkg 2>/dev/null; true

# PluginLauncher pins zOutlookPluginAgent.app (us.zoom.pluginagent) to the user's Dock.
if [[ -x "$SCRIPT_FOLDER/dockutil" ]]; then
    echo "Office-Reset: Removing Zoom Plugin Dock entry"
    /usr/bin/sudo -u "$LoggedInUser" "$SCRIPT_FOLDER/dockutil" --remove us.zoom.pluginagent 2>/dev/null; true
else
    echo "Office-Reset: dockutil not found at $SCRIPT_FOLDER - skipping Dock entry removal"
fi

echo "Office-Reset: Zoom Plugin removal complete for $LoggedInUser"
exit 0
