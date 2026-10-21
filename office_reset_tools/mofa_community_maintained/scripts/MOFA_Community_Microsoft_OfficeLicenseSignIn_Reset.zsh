#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_OfficeLicenseSignIn_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets the Microsoft Office License Sign-in for specific applications.
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          - Replaced eval in SetHomeFolder with safe dscl/path fallback
#          - Removed unused autoload is-at-least
#          - Consolidated seven FindEntry* functions into two generic helpers
#            (FindKeychainEntry / FindKeychainEntryAsUser); while loops now use
#            exit code directly — no echo $? / subshell pattern needed
#          - Fixed FindEntryTeamsIdentity (was running as root; Teams entries live
#            in the user's login keychain — now correctly runs as LoggedInUser)
#          - Added || break to all while-loop deletions to prevent infinite loops
#            on persistent non-404 delete failures
#          - Added 2>/dev/null || true to all single-shot security delete-* calls
#          - Added 2>/dev/null || true to all pkill -HUP calls; added sleep 2
#            after signals so apps quit before keychain operations begin
#          - Quoted $LoggedInUser throughout sudo -u calls
#          - Added [[ -f ... ]] guards before both /bin/mv calls
#          - Replaced find + unquoted sqlite3 with zsh array glob, [1] subscript,
#            existence check, and fully quoted sqlite3 path
#          - Added 2>/dev/null || true to defaults delete; 2>/dev/null || true
#            to killall cfprefsd
#          - All $HOME/... paths converted from backslash-escaped to double-quoted
#          - All system paths with spaces double-quoted
#          - All [ ] / = "" / != "" → [[ ]] / -z / -n throughout
# ============================================================


echo "Office-Reset: Starting postinstall for Reset_Credentials"

GetLoggedInUser() {
	LOGGEDIN=$(/bin/echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/Name /&&!/loginwindow/{print $3}')
	if [[ -z "$LOGGEDIN" ]]; then
		echo "$USER"
	else
		echo "$LOGGEDIN"
	fi
}

SetHomeFolder() {
	# Use dscl to resolve home directory; fall back to /Users/<username>
	HOME=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | sed -n 's/^NFSHomeDirectory: //p')
	if [[ -z "$HOME" ]]; then
		HOME="/Users/$1"
	fi
}

# Generic keychain find helpers — return exit code directly so while loops
# can use them as conditions without a subshell or echo $? wrapper.
FindKeychainEntry() { # $1: flag (-G / -l / -s), $2: value
	/usr/bin/security find-generic-password "$1" "$2" 2>/dev/null 1>/dev/null
}

FindKeychainEntryAsUser() { # $1: flag (-G / -l / -s), $2: value
	/usr/bin/sudo -u "$LoggedInUser" \
		/usr/bin/security find-generic-password "$1" "$2" 2>/dev/null 1>/dev/null
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Quitting all apps gracefully"
# Send SIGHUP for graceful quit; suppress noise if process not running.
# Allow 2 seconds for apps to quit before keychain operations begin.
/usr/bin/pkill -HUP "Microsoft Word"       2>/dev/null || true
/usr/bin/pkill -HUP "Microsoft Excel"      2>/dev/null || true
/usr/bin/pkill -HUP "Microsoft PowerPoint" 2>/dev/null || true
/usr/bin/pkill -HUP "Microsoft Outlook"    2>/dev/null || true
/usr/bin/pkill -HUP "Microsoft OneNote"    2>/dev/null || true
sleep 2

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [[ -z "$KeychainHasLogin" ]]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "${HOME}/Library/Keychains/login.keychain-db"
fi

echo "Office-Reset: Listing keychains for logged-in user"
/usr/bin/security list-keychains

echo "Office-Reset: Removing keychain entries"

# Single-entry deletions — suppress "not found" errors with 2>/dev/null || true
/usr/bin/security delete-generic-password  -s 'OneAuthAccount'                               2>/dev/null || true
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeADAL'                      2>/dev/null || true
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeLiveId'                    2>/dev/null || true

# Multi-entry loops — security deletes one at a time; loop until none remain.
# || break exits the loop if deletion fails for a reason other than "not found".
while FindKeychainEntry -G 'MSOpenTech.ADAL.1'; do
	/usr/bin/security delete-generic-password -G 'MSOpenTech.ADAL.1' 2>/dev/null || break
done

/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 2'          2>/dev/null || true
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 3'          2>/dev/null || true
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 2'       2>/dev/null || true
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 3'       2>/dev/null || true
/usr/bin/security delete-generic-password -l 'Microsoft Office Ticket Cache'                2>/dev/null || true
/usr/bin/security delete-generic-password -l 'Microsoft Office Ticket Cache 2'              2>/dev/null || true
/usr/bin/security delete-generic-password -l 'com.microsoft.adalcache'                      2>/dev/null || true

while FindKeychainEntry -G 'Microsoft Office Data'; do
	/usr/bin/security delete-generic-password -G 'Microsoft Office Data' 2>/dev/null || break
done

/usr/bin/security delete-generic-password -l 'com.microsoft.OutlookCore.Secret'             2>/dev/null || true

while FindKeychainEntry -l 'com.helpshift.data_com.microsoft.Outlook'; do
	/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook' 2>/dev/null || break
done
while FindKeychainEntry -l 'MicrosoftOfficeRMSCredential'; do
	/usr/bin/security delete-generic-password -l 'MicrosoftOfficeRMSCredential' 2>/dev/null || break
done
while FindKeychainEntry -l 'MSProtection.framework.service'; do
	/usr/bin/security delete-generic-password -l 'MSProtection.framework.service' 2>/dev/null || break
done
while FindKeychainEntry -l 'Exchange'; do
	/usr/bin/security delete-generic-password -l 'Exchange' 2>/dev/null || break
done

# Teams keychain entries live in the user's login keychain — must run as LoggedInUser.
while FindKeychainEntryAsUser -l 'Microsoft Teams Identities Cache'; do
	/usr/bin/sudo -u "$LoggedInUser" \
		/usr/bin/security delete-generic-password -l 'Microsoft Teams Identities Cache' 2>/dev/null || break
done
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'Teams Safe Storage'                           2>/dev/null || true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'Microsoft Teams (work or school) Safe Storage' 2>/dev/null || true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'teamsIv'                                       2>/dev/null || true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'teamsKey'                                      2>/dev/null || true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'com.microsoft.teams.HockeySDK'                 2>/dev/null || true
/usr/bin/sudo -u "$LoggedInUser" /usr/bin/security delete-generic-password -l 'com.microsoft.teams.helper.HockeySDK'          2>/dev/null || true

# OneDrive keychain entries
/usr/bin/security delete-generic-password  -l 'com.microsoft.OneDrive.FinderSync.HockeySDK'           2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'com.microsoft.OneDrive.HockeySDK'                      2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'com.microsoft.OneDriveUpdater.HockeySDK'               2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'com.microsoft.OneDriveStandaloneUpdater.HockeySDK'     2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'OneDrive Standalone Cached Credential Business - Business1' 2>/dev/null || true
/usr/bin/security delete-generic-password  -l 'OneDrive Standalone Cached Credential'                 2>/dev/null || true
/usr/bin/security delete-generic-password  -s 'com.microsoft.onedrive.cookies'                        2>/dev/null || true
# OneAuthAccount appears in both Office and OneDrive contexts; delete once per context.
/usr/bin/security delete-generic-password  -s 'OneAuthAccount'                                        2>/dev/null || true

echo "Office-Reset: Removing credential and license files"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/mip_policy"
/bin/rm -f  "${HOME}/Library/Group Containers/UBF8T346G9.Office/DRM_Evo.plist"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

# Remove old .bak backup, then create a fresh .backup of the licensing plist.
/bin/rm -f "/Library/Preferences/com.microsoft.office.licensingV2.plist.bak"
if [[ -f "/Library/Preferences/com.microsoft.office.licensingV2.plist" ]]; then
	/bin/mv "/Library/Preferences/com.microsoft.office.licensingV2.plist" \
		"/Library/Preferences/com.microsoft.office.licensingV2.backup"
fi

/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365.plist"
/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365V2.plist"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365.plist"
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

/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.msa-login-hint.plist"

echo "Office-Reset: Changing preferences"
if [[ -e "${HOME}/Library/Preferences/com.microsoft.office.plist" ]]; then
	/usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults delete "${HOME}/Library/Preferences/com.microsoft.office" OfficeActivationEmailAddress 2>/dev/null || true
	/usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" OfficeAutoSignIn                  -bool TRUE
	/usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" HasUserSeenFREDialog               -bool TRUE
	/usr/bin/sudo -u "$LoggedInUser" /usr/bin/defaults write  "${HOME}/Library/Preferences/com.microsoft.office" HasUserSeenEnterpriseFREDialog      -bool TRUE
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

# Remove ADAL universal storage tokens directly from keychain-2.db.
# Use a zsh array glob to locate the database; [1] guards against multiple matches.
local -a keychain_candidates
keychain_candidates=("${HOME}/Library/Keychains/"**/keychain-2.db(N))
if [[ -f "${keychain_candidates[1]}" ]]; then
	/usr/bin/sqlite3 "${keychain_candidates[1]}" \
		"DELETE FROM genp WHERE agrp='UBF8T346G9.com.microsoft.identity.universalstorage';"
else
	echo "Office-Reset: keychain-2.db not found; skipping ADAL token removal"
fi

/bin/rm -f "${HOME}/Library/Keychains/Microsoft_Entity_Certificates-db"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg"

/usr/bin/killall cfprefsd 2>/dev/null || true

exit 0
