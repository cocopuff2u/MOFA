#!/bin/zsh
# shellcheck shell=zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Teams_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets Microsoft Teams
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.0.1 - @Theile additions to use shellcheck, define PATH, and preserve Teams backgrounds.
#          Classic Teams is dead.
# 1.0.2 - @Theile addition to read arguments with variables (INSTALL=force will always
#          remove the installed version), reset TCC. Open window for user to allow
#          Screen Recording after TCC reset.
# 1.1.0 - Code review and hardening:
#          - Fixed shellcheck pragma from shell=bash to shell=zsh
#          - Replaced eval-based argument parsing with safe key=value case statement
#            (eliminates code-injection risk from arbitrary Jamf script arguments)
#          - Replaced eval in SetHomeFolder with safe dscl/path fallback
#          - Replaced su in open_systempreferences with runAsUser (consistent, more
#            reliable in MDM context)
#          - Fixed FindEntryTeamsIdentity to use runAsUser (was running find as root
#            while delete ran as user — inconsistent keychain search scope)
#          - Simplified while loop: FindEntryTeamsIdentity now returns exit code
#            directly, eliminating subshell + echo $? + numeric comparison
#          - Fixed RepairApp: CDN_PKG_SIZE and download now use $CDN_PKG_URL
#            (was using $DOWNLOAD_URL, causing extra redirect round-trip)
#          - Removed redundant sudo from installer call (script runs as root)
#          - Fixed unquoted variable expansions throughout
#          - Removed unnecessary cd subshell in stat call
#          - Fixed pkgutil awk ambiguous quoting
#          - Changed failure exit 0 → exit 1 in RepairApp
#          - Send SIGTERM before SIGKILL when quitting Teams
#          - Added 2>/dev/null || true to single-shot security delete calls
#          - Added "Office-Reset:" prefix to echo statements missing it
#          - Quoted all $HOME, $TMPDIR, and system library paths
#          - Quoted LoggedInUser/LoggedInUserID in runAsUser and chown calls
#          - Simplified redundant [ -e path ] && rm -rf path → rm -rf path
# ============================================================

# Set PATH variable to SIP-protected folders
export PATH=/usr/bin:/bin:/usr/sbin:/sbin

echo "Office-Reset: Starting Reset_Teams"
autoload is-at-least
APP_NAME="Microsoft Teams"
# DOWNLOAD_URL_TEAMS="https://go.microsoft.com/fwlink/?linkid=869428" # Old Classic URL
DOWNLOAD_URL_TEAMS="https://go.microsoft.com/fwlink/?linkid=2249065"
INSTALLATION_RETRIES=5
OS_VERSION=$(sw_vers -productVersion)
INSTALL="" # "force" will always delete and reinstall to the latest version of Teams

# MARK: Parse arguments

if [[ "$1" == "/" ]]; then
    # Jamf sends '/' as the first argument (mount point)
    echo "Office-Reset: Shifting arguments for Jamf"
    shift 3
fi

# Safely parse key=value arguments — only whitelisted variables are accepted
while [[ -n "$1" ]]; do
    if [[ "$1" == *=* ]]; then
        _arg_key="${1%%=*}"
        _arg_value="${1#*=}"
        case "$_arg_key" in
            INSTALL)
                echo "Office-Reset: Setting ${_arg_key}=${_arg_value}"
                INSTALL="$_arg_value"
                ;;
            *)
                echo "Office-Reset: Ignoring unknown argument: ${_arg_key}"
                ;;
        esac
    fi
    shift 1
done


# MARK: Functions

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
    LoggedInUserID=$(id -u "$1")
}

runAsUser() {
    launchctl asuser "$LoggedInUserID" sudo -u "$LoggedInUser" "$@"
}

open_systempreferences() {
    local preferenceID="$1"
    echo "Office-Reset: Opening system preferences: x-apple.systempreferences:${preferenceID}"
    runAsUser open -u "x-apple.systempreferences:${preferenceID}"
}

RepairApp() {
    DOWNLOAD_URL="$1"
    DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
    if [[ -d "${DOWNLOAD_FOLDER}" ]]; then
        /bin/rm -rf "${DOWNLOAD_FOLDER}"
    fi
    mkdir -p "${DOWNLOAD_FOLDER}"

    CDN_PKG_URL=$(/usr/bin/nscurl --location --head "${DOWNLOAD_URL}" --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
    CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

    CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head "${CDN_PKG_URL}" --dump-header - | awk '/Content-Length:/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    CDN_PKG_MB=$(( CDN_PKG_SIZE / 1024 / 1024 ))
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

# Returns 0 (found) or non-zero (not found) — called directly as while condition
FindEntryTeamsIdentity() {
    runAsUser /usr/bin/security find-generic-password -l 'Microsoft Teams Identities Cache' \
        2>/dev/null 1>/dev/null
}

## MARK: Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser ($LoggedInUserID); Home Folder: $HOME"

# Attempt graceful quit first, then force-kill if still running
/usr/bin/pkill "Microsoft Teams" 2>/dev/null && sleep 2
/usr/bin/pkill -9 "Microsoft Teams" 2>/dev/null || true

# MARK: Handle previous installation of Teams (if any)
appPath="/Applications/Microsoft Teams.app"
if [[ -d "${appPath}" ]]; then
    APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
    APP_BUNDLEID=$(defaults read "${appPath}/Contents/Info.plist" CFBundleIdentifier)
    echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME} with bundle ID ${APP_BUNDLEID}"
    if ! is-at-least 23247.0 "${APP_VERSION}" && is-at-least 10.15 "${OS_VERSION}"; then
        echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Removing it now"
        /bin/rm -rf "${appPath}"
    elif [[ "${INSTALL}" == "force" ]]; then
        echo "Office-Reset: Force reinstall of ${APP_NAME}. Removing it now"
        /bin/rm -rf "${appPath}"
    else
        echo "Office-Reset: The installed version of ${APP_NAME} is ${APP_VERSION}. Should be fine"
    fi
fi
appPath="/Applications/Microsoft Teams classic.app"
if [[ -d "${appPath}" ]]; then
    echo "Office-Reset: Found ancient version of ${APP_NAME}: ${appPath}. Removing it now"
    /bin/rm -rf "${appPath}"
fi
appPath="/Applications/Microsoft Teams (work or school).app"
if [[ -d "${appPath}" ]]; then
    echo "Office-Reset: Found ancient version of ${APP_NAME}: ${appPath}. Removing it now"
    /bin/rm -rf "${appPath}"
fi

# MARK: Handling user-installed backgrounds
# Move backgrounds for Teams Classic (dead)
backgroundsFolder="${HOME}/Library/Application Support/Microsoft/Teams/Backgrounds"
if [[ -d "${backgroundsFolder}" ]]; then
    echo "Office-Reset: Detected Classic backgrounds for ${APP_NAME}"
    destFolder="${HOME}/Teams_Old_Backgrounds"
    orgDestFolder="${destFolder}"
    folderCounter=0
    while [[ -e "${destFolder}" ]]; do
        (( folderCounter++ ))
        destFolder="${orgDestFolder}${folderCounter}"
    done
    echo "Office-Reset: Moving Classic backgrounds to ${destFolder}"
    mv "${backgroundsFolder}" "${destFolder}"
    runAsUser open "${destFolder}"
fi
# Preserve new Teams backgrounds before wiping Containers
backgroundsFolder="${HOME}/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/Backgrounds"
if [[ -d "${backgroundsFolder}" ]]; then
    echo "Office-Reset: Preserving backgrounds for ${APP_NAME}"
    mv "${backgroundsFolder}" /tmp/
fi

# MARK: Remove configuration data
echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -rf "${HOME}/Library/Application Support/Teams"
/bin/rm -rf "${HOME}/Library/Application Support/Microsoft/Teams"

/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.teams"
/bin/rm -rf "${HOME}/Library/Application Support/com.microsoft.teams.helper"

/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.com.microsoft.teams"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.teams2"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.teams2.launcher"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.teams2.notificationcenter"

/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.teams"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.teams.helper"
/bin/rm -f  "${HOME}/Library/Cookies/com.microsoft.teams.binarycookies"
/bin/rm -f  "${HOME}/Library/HTTPStorages/com.microsoft.teams.binarycookies"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.teams"
/bin/rm -rf "${HOME}/Library/Logs/Microsoft Teams"
/bin/rm -rf "${HOME}/Library/Logs/Microsoft Teams Helper"
/bin/rm -rf "${HOME}/Library/Logs/Microsoft Teams Helper (Renderer)"
/bin/rm -rf "${HOME}/Library/Saved Application State/com.microsoft.teams.savedState"
/bin/rm -rf "${HOME}/Library/WebKit/com.microsoft.teams"

/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.teams2"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.teams2.launcher"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.teams2.notificationcenter"

/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.com.microsoft.teams"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

/bin/rm -rf "/Library/Application Support/TeamsUpdaterDaemon"
/bin/rm -rf "/Library/Application Support/Microsoft/TeamsUpdaterDaemon"
/bin/rm -rf "/Library/Application Support/Teams"

/bin/rm -f  "${HOME}/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f  "/Library/Managed Preferences/com.microsoft.teams.plist"
/bin/rm -f  /Library/Preferences/com.microsoft.teams.plist
/bin/rm -f  "${HOME}/Library/Preferences/com.microsoft.teams.helper.plist"
/bin/rm -f  "/Library/Managed Preferences/com.microsoft.teams.helper.plist"
/bin/rm -f  /Library/Preferences/com.microsoft.teams.helper.plist

/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.teams"
/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.teams Crashes"
/bin/rm -rf "${TMPDIR:-/tmp}/Teams"
/bin/rm -rf "${TMPDIR:-/tmp}/Microsoft Teams Helper (Renderer)"
/bin/rm -rf "${TMPDIR:-/tmp}/v8-compile-cache-501"

/bin/rm -rf /Library/Logs/Microsoft/Teams


# MARK: Extra things to clean
# Reset TCC (PPPC) for Teams
echo "Office-Reset: Resetting TCC for com.microsoft.teams2"
tccutil reset All com.microsoft.teams2

# Keychain items
KeychainHasLogin=$(runAsUser /usr/bin/security list-keychains | grep 'login.keychain')
if [[ -z "$KeychainHasLogin" ]]; then
    echo "Office-Reset: Adding user login keychain to list"
    runAsUser /usr/bin/security list-keychains -s "${HOME}/Library/Keychains/login.keychain-db"
fi

echo "Office-Reset: Listing keychains for logged-in user"
runAsUser /usr/bin/security list-keychains

while FindEntryTeamsIdentity; do
    runAsUser /usr/bin/security delete-generic-password -l 'Microsoft Teams Identities Cache' \
        2>/dev/null || break
done
runAsUser /usr/bin/security delete-generic-password -l 'Teams Safe Storage'                             2>/dev/null || true
runAsUser /usr/bin/security delete-generic-password -l 'Microsoft Teams (work or school) Safe Storage' 2>/dev/null || true
runAsUser /usr/bin/security delete-generic-password -l 'teamsIv'                                       2>/dev/null || true
runAsUser /usr/bin/security delete-generic-password -l 'teamsKey'                                      2>/dev/null || true
runAsUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.HockeySDK'                 2>/dev/null || true
runAsUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.helper.HockeySDK'          2>/dev/null || true

# Restore backgrounds
if [[ -d "/tmp/Backgrounds" ]]; then
    echo "Office-Reset: Restoring backgrounds for ${APP_NAME}"
    runAsUser mkdir -p "${HOME}/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/"
    mv /tmp/Backgrounds "${HOME}/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/"
    chown -R "$LoggedInUser" "${HOME}/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams"
fi


# MARK: Install Teams if damaged or not found
appPath="/Applications/Microsoft Teams.app"
if ! codesign -vv --deep "${appPath}" 2>&1; then
    echo "Office-Reset: ${APP_NAME} is damaged or not present; preparing for reinstallation"
    /bin/rm -rf "${appPath}"
else
    echo "Office-Reset: Codesign passed successfully"
    APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
    echo "Office-Reset: The installed version of ${APP_NAME} is ${APP_VERSION}"
fi
folderCounter=1
while [[ ! -d "${appPath}" ]]; do
    echo "Office-Reset: ${APP_NAME} not installed. Attempt ${folderCounter} of ${INSTALLATION_RETRIES}"
    RepairApp "$DOWNLOAD_URL_TEAMS"
    codesign -vv --deep "${appPath}" 2>&1
    if [[ $? -gt 0 ]]; then
        echo "Office-Reset: The ${APP_NAME} app bundle is damaged; removing for reinstallation"
        /bin/rm -rf "${appPath}"
    else
        echo "Office-Reset: Codesign passed successfully"
        APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
        echo "Office-Reset: The installed version of ${APP_NAME} is now ${APP_VERSION}"
    fi
    [[ $folderCounter -ge $INSTALLATION_RETRIES ]] && break
    (( folderCounter++ ))
done

# Open Privacy & Security so the user can re-grant Screen Recording
open_systempreferences "com.apple.preference.security?Privacy_ScreenCapture"

exit 0
