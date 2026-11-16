#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_SkypeForBusiness_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the Microsoft Skype For Business application
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Fixed $HOME variable shadowing (renamed to $UserHome); removed unused autoload;
#          updated conditionals to zsh-native [[ ]]; fixed security commands to run in
#          logged-in user context; fixed keychain check user context; added cfprefsd flush;
#          corrected -rf flag on plist file to -f; added dockutil existence check;
#          added missing SfB data paths (caches, cookies, saved state).
#
# 1.2.0 - Removed `security list-keychains -s`, which overwrote the user's keychain search
#          list. All security calls now pass the user's login keychain path explicitly.
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_SkypeForBusiness"

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
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $UserHome"

echo "Office-Reset: Stopping Skype for Business"
/usr/bin/pkill -9 'Skype for Business'

# Flush cfprefsd cache before removing preference plists.
# Without this, cfprefsd may recreate plists from its in-memory cache after deletion.
/usr/bin/killall cfprefsd 2>/dev/null; true

echo "Office-Reset: Removing Skype for Business preferences"
/bin/rm -f  "$UserHome/Library/Preferences/com.microsoft.OutlookSkypeIntegration.plist"
/bin/rm -f  "$UserHome/Library/Preferences/com.microsoft.SkypeForBusiness.plist"
/bin/rm -f  "/Library/Preferences/com.microsoft.SkypeForBusiness.plist"
/bin/rm -f  "/Library/Managed Preferences/com.microsoft.SkypeForBusiness.plist"

echo "Office-Reset: Removing Skype for Business data"
/bin/rm -rf "$UserHome/Library/Application Scripts/com.microsoft.SkypeForBusiness"
/bin/rm -rf "$UserHome/Library/Containers/com.microsoft.SkypeForBusiness"
/bin/rm -rf "$UserHome/Library/Application Support/Microsoft/SkypeForBusiness"

echo "Office-Reset: Removing Skype for Business caches and ancillary data"
/bin/rm -rf "$UserHome/Library/Caches/com.microsoft.SkypeForBusiness"
/bin/rm -rf "$UserHome/Library/Saved Application State/com.microsoft.SkypeForBusiness.savedState"
/bin/rm -f  "$UserHome/Library/Cookies/com.microsoft.SkypeForBusiness.binarycookies"

echo "Office-Reset: Removing Skype for Business app"
/bin/rm -rf "/Applications/Skype for Business.app"

echo "Office-Reset: Removing package receipts"
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_AU_Bootstrapper.app
/usr/sbin/pkgutil --forget com.microsoft.SkypeForBusiness

# Remove Skype for Business keychain entries.
# Run as the logged-in user so the correct login keychain is targeted.
# (Running security commands as root targets root's keychain, not the user's.)
echo "Office-Reset: Removing Skype for Business keychain entries"
# Target the user's login keychain explicitly on every security command.
# Do NOT use `security list-keychains -s`: run as root it rewrites root's keychain
# search list, which breaks the jamf binary (Device Signature Error / -25293).
UserKeychain="${UserHome}/Library/Keychains/login.keychain-db"
if [[ ! -f "$UserKeychain" ]]; then
    echo "Office-Reset: WARNING - user login keychain not found at $UserKeychain"
fi
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'com.microsoft.SkypeForBusiness.HockeySDK' "$UserKeychain" 2>/dev/null; true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'Skype for Business' "$UserKeychain" 2>/dev/null; true

# Remove Dock entry via dockutil if available alongside this script.
if [[ -x "$SCRIPT_FOLDER/dockutil" ]]; then
    echo "Office-Reset: Removing Skype for Business Dock entry"
    /usr/bin/sudo -u "$LoggedInUser" "$SCRIPT_FOLDER/dockutil" --remove com.microsoft.SkypeForBusiness
else
    echo "Office-Reset: dockutil not found at $SCRIPT_FOLDER — skipping Dock entry removal"
fi

echo "Office-Reset: Skype for Business removal complete for $LoggedInUser"
exit 0
