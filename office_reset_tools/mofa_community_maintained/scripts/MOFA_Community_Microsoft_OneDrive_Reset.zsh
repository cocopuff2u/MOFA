#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_OneDrive_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets Microsoft OneDrive
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          [Fix]  SetHomeFolder: replaced unsafe eval with dscl + /Users/<user> fallback
#          [Fix]  RepairApp: second nscurl HEAD call and download now use resolved
#                 $CDN_PKG_URL (not $DOWNLOAD_URL) — avoids following the redirect twice
#                 and ensures Content-Length is read from the actual CDN response
#          [Fix]  RepairApp: removed cd subshell in stat call; use full path directly
#          [Fix]  RepairApp: removed redundant sudo from installer (script runs as root)
#          [Fix]  RepairApp: failure paths changed from exit 0 to exit 1 for correct
#                 error signalling to Jamf
#          [Fix]  RepairApp: unquoted $DOWNLOAD_URL / $CDN_PKG_URL / $DOWNLOAD_FOLDER
#                 in nscurl, installer, pkgutil, and stat calls — now fully quoted
#          [Fix]  RepairApp: pkgutil awk pattern cleaned up (ambiguous shell quoting)
#          [Fix]  Codesign check: combined two-pass run into single captured call
#                 (stderr included via 2>&1); avoids re-running codesign just to get
#                 the error message
#          [Fix]  pkill: SIGTERM before SIGKILL with sleep 2; 2>/dev/null || true
#                 suppresses "no matching processes" noise
#          [Fix]  All $HOME/... rm paths: consistently double-quoted with "${HOME}/...";
#                 removed mixed backslash-escaping throughout
#          [Fix]  Duplicate /bin/rm -f /Library/Preferences/com.microsoft.OneDrive.plist
#                 (appeared on both line 179 and 182) — duplicate removed
#          [Fix]  security delete-generic-password: added 2>/dev/null || true on all
#                 calls to suppress "not found" stderr noise
#          [Fix]  find + sqlite3 for keychain-2.db: replaced find with a zsh glob;
#                 quoted $KEYCHAIN_2_PATH; added existence check before sqlite3 call;
#                 used array [1] subscript to safely handle multiple keychain databases
#          [Opt]  /bin/expr replaced with native zsh arithmetic $(( ))
#          [Opt]  All [ ] single-bracket tests replaced with [[ ]]; = "" / != ""
#                 replaced with -z / -n
#          [Opt]  Echo on "Display list-keychains" given consistent "Office-Reset:" prefix
# ============================================================

echo "Office-Reset: Starting postinstall for Reset_OneDrive"
autoload is-at-least
APP_NAME="Microsoft OneDrive"
DOWNLOAD_URL="https://go.microsoft.com/fwlink/?linkid=861011"
OS_VERSION=$(sw_vers -productVersion)

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
    HOME=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | sed -n 's/^NFSHomeDirectory: //p')
    if [[ -z "$HOME" ]]; then
        HOME="/Users/$1"
    fi
}

RepairApp() {
    DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
    if [[ -d "${DOWNLOAD_FOLDER}" ]]; then
        /bin/rm -rf "${DOWNLOAD_FOLDER}"
    fi
    mkdir -p "${DOWNLOAD_FOLDER}"

    # Resolve the redirect once and reuse the CDN URL for all subsequent operations
    CDN_PKG_URL=$(/usr/bin/nscurl --location --head "${DOWNLOAD_URL}" --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
    CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

    # Use the resolved CDN URL directly — avoids following the redirect a second time
    CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head "${CDN_PKG_URL}" --dump-header - | awk '/Content-Length/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    CDN_PKG_MB=$(( CDN_PKG_SIZE / 1000 / 1000 ))
    echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

    echo "Office-Reset: Starting ${APP_NAME} package download"
    /usr/bin/nscurl --background --download --large-download --location \
        --download-directory "${DOWNLOAD_FOLDER}" "${CDN_PKG_URL}"
    echo "Office-Reset: Finished package download"

    LOCAL_PKG_SIZE=$(stat -qf%z "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}")
    if [[ "${LOCAL_PKG_SIZE}" == "${CDN_PKG_SIZE}" ]]; then
        echo "Office-Reset: Downloaded package is wholesome"
    else
        echo "Office-Reset: Downloaded package is malformed. Local file size: ${LOCAL_PKG_SIZE}"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi

    LOCAL_PKG_SIGNING=$(/usr/sbin/pkgutil --check-signature "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}" | awk '/Developer ID Installer/' | cut -d ':' -f2 | awk '{$1=$1};1')
    if [[ "${LOCAL_PKG_SIGNING}" == "Microsoft Corporation (UBF8T346G9)" ]]; then
        echo "Office-Reset: Downloaded package is signed by Microsoft"
    else
        echo "Office-Reset: Downloaded package is not signed by Microsoft"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi

    echo "Office-Reset: Starting package install"
    /usr/sbin/installer -pkg "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}" -target /
    if [[ $? -eq 0 ]]; then
        echo "Office-Reset: Package installed successfully"
    else
        echo "Office-Reset: Package installation failed"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

# Attempt graceful quit first, then force-kill if processes are still running
/usr/bin/pkill 'OneDrive'                   2>/dev/null || true
/usr/bin/pkill 'FinderSync'                 2>/dev/null || true
/usr/bin/pkill 'OneDriveStandaloneUpdater'  2>/dev/null || true
/usr/bin/pkill 'OneDriveUpdater'            2>/dev/null || true
sleep 2
/usr/bin/pkill -9 'OneDrive'                  2>/dev/null || true
/usr/bin/pkill -9 'FinderSync'                2>/dev/null || true
/usr/bin/pkill -9 'OneDriveStandaloneUpdater' 2>/dev/null || true
/usr/bin/pkill -9 'OneDriveUpdater'           2>/dev/null || true

if [[ -d "/Applications/OneDrive.app" ]]; then
    APP_VERSION=$(defaults read "/Applications/OneDrive.app/Contents/Info.plist" CFBundleVersion)
    echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
    if ! is-at-least 23154.0 "${APP_VERSION}" && is-at-least 10.15 "${OS_VERSION}"; then
        echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Updating it now"
        RepairApp
    fi
    echo "Office-Reset: Checking the app bundle for corruption"
    CODESIGN_RESULT=$(/usr/bin/codesign -vv --deep "/Applications/OneDrive.app" 2>&1)
    if [[ $? -gt 0 ]]; then
        echo "Office-Reset: The ${APP_NAME} app bundle is damaged: ${CODESIGN_RESULT}"
        echo "Office-Reset: The ${APP_NAME} app bundle will be removed and reinstalled"
        /bin/rm -rf "/Applications/OneDrive.app"
        RepairApp
    else
        echo "Office-Reset: Codesign passed successfully"
    fi
else
    echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -rf "${HOME}/Library/Caches/OneDrive"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.OneDrive"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.OneDriveUpdater"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.SyncReporter"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.SharePoint-mac"

/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDriveStandaloneUpdater.binarycookies"

/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.OneDrive"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.OneDrive.binarycookies"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveUpdater"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.SharePoint-mac"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.SharePoint-mac.binarycookies"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.SyncReporter"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.SyncReporter.binarycookies"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater.binarycookies"

/bin/rm -rf "${HOME}/Library/WebKit/com.microsoft.OneDrive"

/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.OneDrive-mac"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.OneDrive.FinderSync"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.OneDrive-mac.FinderSync"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.OneDriveLauncher"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.OneDrive.FileProvider"

/bin/rm -rf "${HOME}/Library/Logs/OneDrive"
/bin/rm -rf "/Library/Logs/Microsoft/OneDrive"

/bin/rm -rf "${HOME}/Library/Application Support/OneDrive"
/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.OneDrive"
/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.OneDriveUpdater"
/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.SharePoint-mac"
/bin/rm -rf "${HOME}/Library/Application Support/OneDriveUpdater"
/bin/rm -rf "${HOME}/Library/Application Support/OneDriveStandaloneUpdater"

/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.OneDrive.FinderSync"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.OneDrive.FileProvider"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.OneDriveStandaloneSuite"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.OfficeOneDriveSyncIntegration"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.OneDriveSyncClientSuite"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.Kfm"

/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.OfficeOneDriveSyncIntegration"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.OneDriveStandaloneSuite"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.OneDriveSyncClientSuite"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Kfm"

/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.SharePoint-mac.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.OneDriveUpdater.plist"
/bin/rm -f "${HOME}/Library/Preferences/UBF8T346G9.OneDriveStandaloneSuite.plist"
/bin/rm -f "${HOME}/Library/Preferences/UBF8T346G9.OfficeOneDriveSyncIntegration.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDriveUpdater.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDriveUpdater.plist"

/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.OneDrive"
/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.OneDrive.FinderSync"
/bin/rm -f  "${TMPDIR:-/tmp}/OneDriveVersion.xml"

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [[ -z "$KeychainHasLogin" ]]; then
    echo "Office-Reset: Adding user login keychain to list"
    /usr/bin/security list-keychains -s "${HOME}/Library/Keychains/login.keychain-db"
fi

echo "Office-Reset: Listing keychains for logged-in user"
/usr/bin/security list-keychains

/usr/bin/security delete-generic-password -l 'com.microsoft.OneDrive.FinderSync.HockeySDK'          2>/dev/null || true
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDrive.HockeySDK'                     2>/dev/null || true
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDriveUpdater.HockeySDK'              2>/dev/null || true
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDriveStandaloneUpdater.HockeySDK'    2>/dev/null || true
/usr/bin/security delete-generic-password -l 'OneDrive Standalone Cached Credential Business - Business1' 2>/dev/null || true
/usr/bin/security delete-generic-password -l 'OneDrive Standalone Cached Credential'                2>/dev/null || true
/usr/bin/security delete-generic-password -s 'com.microsoft.onedrive.cookies'                       2>/dev/null || true
/usr/bin/security delete-generic-password -s 'OneAuthAccount'                                       2>/dev/null || true
/usr/bin/security delete-generic-password -l 'com.microsoft.adalcache'                              2>/dev/null || true

/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

# Remove cached ADAL tokens directly from the keychain database.
# Use a zsh glob to locate keychain-2.db (stored under a UUID subdirectory).
# The (N) qualifier suppresses errors if no match is found; [1] selects the
# first result to avoid passing multiple paths to sqlite3.
local -a keychain_candidates
keychain_candidates=("${HOME}/Library/Keychains/"**/keychain-2.db(N))
if [[ -f "${keychain_candidates[1]}" ]]; then
    /usr/bin/sqlite3 "${keychain_candidates[1]}" \
        "DELETE FROM genp WHERE agrp='UBF8T346G9.com.microsoft.identity.universalstorage';"
else
    echo "Office-Reset: keychain-2.db not found; skipping ADAL token removal"
fi

exit 0
