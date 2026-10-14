#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_License_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets the Microsoft License for specific applications.
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          [Fix]  SetHomeFolder: replaced unsafe eval with dscl + /Users/<user> fallback
#          [Fix]  Removed unused autoload is-at-least (not referenced anywhere in script)
#          [Fix]  pkill: added 2>/dev/null || true to suppress "no matching processes"
#                 noise; added sleep 2 after signals to allow apps to quit before
#                 keychain operations begin
#          [Fix]  /bin/mv calls: guarded with [[ -f ]] existence check to prevent
#                 noisy errors when source file is absent
#          [Fix]  sudo -u: quoted $LoggedInUser to handle usernames with spaces;
#                 quoted all $HOME path arguments to defaults commands
#          [Fix]  All security delete-* single calls: added 2>/dev/null || true to
#                 suppress "SecKeychainSearchCopyNext" / "not found" errors
#          [Fix]  security delete-internet-password calls: added 2>/dev/null || true
#          [Fix]  killall cfprefsd: added 2>/dev/null || true
#          [Opt]  Replaced all [ ] single-bracket tests with [[ ]] for consistency
#          [Opt]  All = "" / != "" comparisons replaced with -z / -n
#          [Opt]  Duplicate security delete-generic-password calls consolidated into
#                 DeleteAllKeychainGeneric helper (loops until no entries remain,
#                 which is more robust than a fixed repeat count)
#          [Opt]  Echo on line 55 given consistent "Office-Reset:" prefix
# ============================================================

echo "Office-Reset: Starting postinstall for Reset_Credentials"
# NOTE: autoload is-at-least removed — not used in this script

GetLoggedInUser() {
    LOGGEDIN=$(/bin/echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/Name /&&!/loginwindow/{print $3}')
    if [[ -z "$LOGGEDIN" ]]; then
        echo "$USER"
    else
        echo "$LOGGEDIN"
    fi
}

SetHomeFolder() {
    # Prefer NFSHomeDirectory from dscl; fall back to /Users/<username>
    # NOTE: Using dscl avoids the original eval echo "~$1", which is unsafe if
    # the username contains shell metacharacters.
    HOME=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | awk '{print $NF}')
    if [[ -z "$HOME" ]]; then
        HOME="/Users/$1"
    fi
}

# Helper: delete ALL generic keychain entries matching a flag+value pair.
# The security tool deletes only one matching entry per invocation; this loop
# continues until no matching entries remain (more robust than a fixed repeat count).
DeleteAllKeychainGeneric() {
    local flag="$1" value="$2"
    while /usr/bin/security delete-generic-password "${flag}" "${value}" 2>/dev/null; do
        :
    done
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Quitting all apps gracefully"
# SIGHUP triggers quit for Office apps; suppress noise if no process is running
/usr/bin/pkill -HUP 'Microsoft Word'        2>/dev/null || true
/usr/bin/pkill -HUP 'Microsoft Excel'       2>/dev/null || true
/usr/bin/pkill -HUP 'Microsoft PowerPoint'  2>/dev/null || true
/usr/bin/pkill -HUP 'Microsoft Outlook'     2>/dev/null || true
/usr/bin/pkill -HUP 'Microsoft OneNote'     2>/dev/null || true
# Allow apps to finish quitting before keychain operations begin
sleep 2

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [[ -z "$KeychainHasLogin" ]]; then
    echo "Office-Reset: Adding user login keychain to list"
    /usr/bin/security list-keychains -s "${HOME}/Library/Keychains/login.keychain-db"
fi

echo "Office-Reset: Listing keychains for logged-in user"
/usr/bin/security list-keychains

echo "Office-Reset: Removing keychain entries"

# --- Single-entry deletions (at most one matching entry expected) ---
/usr/bin/security delete-generic-password  -s 'OneAuthAccount'                          2>/dev/null || true
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeADAL'                 2>/dev/null || true
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeLiveId'               2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'Microsoft Office Identities Cache 2'     2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'Microsoft Office Identities Cache 3'     2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'Microsoft Office Identities Settings 2'  2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'Microsoft Office Identities Settings 3'  2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'Microsoft Office Ticket Cache'           2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'com.microsoft.adalcache'                 2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'com.microsoft.OutlookCore.Secret'        2>/dev/null || true

# --- Multi-entry deletions (loop until all matching entries are removed) ---
DeleteAllKeychainGeneric -G 'MSOpenTech.ADAL.1'
DeleteAllKeychainGeneric -G 'Microsoft Office Data'
DeleteAllKeychainGeneric -l 'com.helpshift.data_com.microsoft.Outlook'
DeleteAllKeychainGeneric -l 'MicrosoftOfficeRMSCredential'
DeleteAllKeychainGeneric -l 'MSProtection.framework.service'
DeleteAllKeychainGeneric -l 'Exchange'

echo "Office-Reset: Removing credential and license files"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/mip_policy"
/bin/rm -f  "${HOME}/Library/Group Containers/UBF8T346G9.Office/DRM_Evo.plist"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

# Back up licensingV2 plist instead of deleting it; guard mv to avoid errors if absent
/bin/rm -f "/Library/Preferences/com.microsoft.office.licensingV2.plist.bak"
if [[ -f "/Library/Preferences/com.microsoft.office.licensingV2.plist" ]]; then
    /bin/mv "/Library/Preferences/com.microsoft.office.licensingV2.plist" \
            "/Library/Preferences/com.microsoft.office.licensingV2.backup"
fi

/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365.plist"
/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365V2.plist"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365.plist"

# Back up Office365V2 plist; guard mv to avoid errors if absent
if [[ -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365V2.plist" ]]; then
    /bin/mv "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365V2.plist" \
            "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365V2.backup"
fi

/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.e0E2OUQxNUY1LTAxOUQtNDQwNS04QkJELTAxQTI5M0JBOTk4O.plist"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/e0E2OUQxNUY1LTAxOUQtNDQwNS04QkJELTAxQTI5M0JBOTk4O"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.O4kTOBJ0M5ITQxATLEJkQ40SNwQDNtQUOxATL1YUNxQUO2E0e.plist"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/O4kTOBJ0M5ITQxATLEJkQ40SNwQDNtQUOxATL1YUNxQUO2E0e"

/bin/rm -rf "/Library/Microsoft/Office/Licenses"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/Licenses"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.RMS-XPCService"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.Office365ServiceV2"

/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Word/Data/Library/Application Support/Microsoft"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Excel/Data/Library/Application Support/Microsoft"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Powerpoint/Data/Library/Application Support/Microsoft"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Outlook/Data/Library/Application Support/Microsoft"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.onenote.mac/Data/Library/Application Support/Microsoft"

echo "Office-Reset: Changing preferences"
if [[ -e "${HOME}/Library/Preferences/com.microsoft.office.plist" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults delete "${HOME}/Library/Preferences/com.microsoft.office" OfficeActivationEmailAddress 2>/dev/null || true
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" OfficeAutoSignIn                  -bool TRUE
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" HasUserSeenFREDialog               -bool TRUE
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" HasUserSeenEnterpriseFREDialog     -bool TRUE
fi
if [[ -d "${HOME}/Library/Containers/com.microsoft.Word/Data/Library/Preferences" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write \
        "${HOME}/Library/Containers/com.microsoft.Word/Data/Library/Preferences/com.microsoft.Word" \
        kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [[ -d "${HOME}/Library/Containers/com.microsoft.Excel/Data/Library/Preferences" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write \
        "${HOME}/Library/Containers/com.microsoft.Excel/Data/Library/Preferences/com.microsoft.Excel" \
        kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [[ -d "${HOME}/Library/Containers/com.microsoft.Powerpoint/Data/Library/Preferences" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write \
        "${HOME}/Library/Containers/com.microsoft.Powerpoint/Data/Library/Preferences/com.microsoft.Powerpoint" \
        kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [[ -d "${HOME}/Library/Containers/com.microsoft.Outlook/Data/Library/Preferences" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write \
        "${HOME}/Library/Containers/com.microsoft.Outlook/Data/Library/Preferences/com.microsoft.Outlook" \
        kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [[ -d "${HOME}/Library/Containers/com.microsoft.onenote.mac/Data/Library/Preferences" ]]; then
    /usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write \
        "${HOME}/Library/Containers/com.microsoft.onenote.mac/Data/Library/Preferences/com.microsoft.onenote.mac" \
        kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi

/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg"

/usr/bin/killall cfprefsd 2>/dev/null || true

exit 0
