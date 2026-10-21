#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Outlook_Data_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the Microsoft Outlook Data
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Fixed $HOME variable shadowing (renamed to $UserHome); removed unused autoload;
#          updated conditionals to zsh-native [[ ]]; added cfprefsd flush before plist removal;
#          added missing Outlook data paths (caches, cookies, saved state, legacy app support).
#
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_Outlook_Data"

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

echo "Office-Reset: Stopping Outlook"
/usr/bin/pkill -9 'Microsoft Outlook'

# Flush cfprefsd cache before removing preference plists.
# Without this, cfprefsd may recreate plists from its in-memory cache after deletion.
/usr/bin/killall cfprefsd 2>/dev/null; true

echo "Office-Reset: Removing Outlook preferences"
/bin/rm -f "$UserHome/Library/Preferences/com.microsoft.Outlook.plist"

echo "Office-Reset: Removing Outlook data"
/bin/rm -rf "$UserHome/Library/Group Containers/UBF8T346G9.Office/Outlook"
/bin/rm -f  "$UserHome/Library/Group Containers/UBF8T346G9.Office/OutlookProfile.plist"

# Legacy Outlook data location (Outlook 2016 and earlier)
/bin/rm -rf "$UserHome/Library/Application Support/Microsoft/Outlook"

echo "Office-Reset: Removing Outlook caches and ancillary data"
/bin/rm -rf "$UserHome/Library/Caches/com.microsoft.Outlook"
/bin/rm -rf "$UserHome/Library/WebKit/com.microsoft.Outlook"
/bin/rm -rf "$UserHome/Library/Saved Application State/com.microsoft.Outlook.savedState"
/bin/rm -f  "$UserHome/Library/Cookies/com.microsoft.Outlook.binarycookies"

echo "Office-Reset: Outlook data removal complete for $LoggedInUser"
exit 0
