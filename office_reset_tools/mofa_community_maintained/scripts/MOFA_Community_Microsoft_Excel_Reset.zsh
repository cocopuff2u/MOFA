#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Excel_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets Microsoft Excel
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          [Fix]  SetHomeFolder: replaced unsafe eval with dscl + /Users/<user> fallback
#          [Fix]  GetCustomManifestVersion: initialize CUSTOM_VERSION/FULL_UPDATER to ""
#                 on each call to prevent stale values across multiple invocations
#          [Fix]  RepairApp: removed redundant sudo from installer (script runs as root)
#          [Fix]  RepairApp: failure paths now exit 1 instead of exit 0 so Jamf can
#                 detect and report policy failures
#          [Fix]  Codesign check: combined two codesign invocations into one; output
#                 now captures stderr (2>&1) so CODESIGN_RESULT is actually populated
#          [Fix]  pkgutil awk: cleaned up ambiguous single-quote/slash quoting
#          [Fix]  stat: removed unnecessary cd subshell; use full path directly
#          [Opt]  pkill: send SIGTERM first, sleep 2, then SIGKILL; suppress "no
#                 matching processes" noise with 2>/dev/null
#          [Opt]  Replaced /bin/expr integer division with native zsh $(( )) arithmetic
#          [Opt]  All [ ] single-bracket tests → [[ ]] for consistency with rest of script
#          [Opt]  All = "" / != "" string comparisons → -z / -n
#          [Opt]  All backslash-escaped path spaces → double-quoted paths throughout
#          [Opt]  Unquoted variable expansions in nscurl/installer/rm/pkgutil → quoted
#          [Opt]  Glob patterns in rm commands use (N) qualifier to avoid "no matches
#                 found" errors when target directories are empty
# ============================================================

echo "Office-Reset: Starting postinstall for Reset_Excel"
autoload is-at-least
APP_NAME="Microsoft Excel"
APP_GENERATION="2019"
DOWNLOAD_2019="https://go.microsoft.com/fwlink/?linkid=525135"
DOWNLOAD_2016="https://go.microsoft.com/fwlink/?linkid=871750"
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

GetPrefValue() { # $1: domain, $2: key
    osascript -l JavaScript << EndOfScript
    ObjC.import('Foundation');
    ObjC.unwrap($.NSUserDefaults.alloc.initWithSuiteName('$1').objectForKey('$2'))
EndOfScript
}

GetCustomManifestVersion() {
    # Reset globals on every call to prevent stale values if called more than once
    CUSTOM_VERSION=""
    FULL_UPDATER=""

    CHANNEL_NAME=$(GetPrefValue "com.microsoft.autoupdate2" "ChannelName")
    if [[ "${CHANNEL_NAME}" == "Custom" ]]; then
        MANIFEST_SERVER=$(GetPrefValue "com.microsoft.autoupdate2" "ManifestServer")
        echo "Office-Reset: Found custom ManifestServer ${MANIFEST_SERVER}"
        FULL_UPDATER=$(/usr/bin/nscurl --location "${MANIFEST_SERVER}/0409XCEL2019.xml" \
            | grep -A1 -m1 'FullUpdaterLocation' \
            | grep 'string' \
            | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
        echo "Office-Reset: Found custom FullUpdaterLocation ${FULL_UPDATER}"
        if [[ "${FULL_UPDATER}" == "https://"* ]]; then
            CUSTOM_VERSION=$(/usr/bin/nscurl --location "${MANIFEST_SERVER}/0409XCEL2019-chk.xml" \
                | grep -A1 -m1 'Update Version' \
                | grep 'string' \
                | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
            echo "Office-Reset: Found custom update version ${CUSTOM_VERSION}"
        fi
    fi
}

RepairApp() {
    if [[ "${APP_GENERATION}" == "2016" ]]; then
        DOWNLOAD_URL="${DOWNLOAD_2016}"
    else
        DOWNLOAD_URL="${DOWNLOAD_2019}"
    fi

    DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
    if [[ -d "${DOWNLOAD_FOLDER}" ]]; then
        /bin/rm -rf "${DOWNLOAD_FOLDER}"
    fi
    mkdir -p "${DOWNLOAD_FOLDER}"

    GetCustomManifestVersion
    if [[ -z "${CUSTOM_VERSION}" ]]; then
        CDN_PKG_URL=$(/usr/bin/nscurl --location --head "${DOWNLOAD_URL}" --dump-header - \
            | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    else
        CDN_PKG_URL="${FULL_UPDATER}"
    fi

    echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
    CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

    CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head "${CDN_PKG_URL}" --dump-header - \
        | awk '/Content-Length/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
    # Use native zsh arithmetic instead of /bin/expr
    CDN_PKG_MB=$(( CDN_PKG_SIZE / 1000 / 1000 ))
    echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

    echo "Office-Reset: Starting ${APP_NAME} package download"
    /usr/bin/nscurl --background --download --large-download --location \
        --download-directory "${DOWNLOAD_FOLDER}" "${CDN_PKG_URL}"
    echo "Office-Reset: Finished package download"

    # Use full path directly; no need for a cd subshell
    LOCAL_PKG_SIZE=$(stat -qf%z "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}")
    if [[ "${LOCAL_PKG_SIZE}" == "${CDN_PKG_SIZE}" ]]; then
        echo "Office-Reset: Downloaded package is wholesome"
    else
        echo "Office-Reset: Downloaded package is malformed. Local file size: ${LOCAL_PKG_SIZE}"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi

    LOCAL_PKG_SIGNING=$(/usr/sbin/pkgutil --check-signature "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}" \
        | awk '/Developer ID Installer/' \
        | cut -d ':' -f2 \
        | awk '{$1=$1};1')
    if [[ "${LOCAL_PKG_SIGNING}" == "Microsoft Corporation (UBF8T346G9)" ]]; then
        echo "Office-Reset: Downloaded package is signed by Microsoft"
    else
        echo "Office-Reset: Downloaded package is not signed by Microsoft"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi

    echo "Office-Reset: Starting package install"
    # sudo is unnecessary — this script runs as root via Jamf postinstall
    /usr/sbin/installer -pkg "${DOWNLOAD_FOLDER}${CDN_PKG_NAME}" -target /
    if [[ $? -eq 0 ]]; then
        echo "Office-Reset: Package installed successfully"
    else
        echo "Office-Reset: Package installation failed"
        echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
        exit 1
    fi
    echo "Office-Reset: Exiting without removing configuration data"
    exit 0
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

# Graceful SIGTERM first; wait 2s only if something was running, then SIGKILL
/usr/bin/pkill "Microsoft Excel" 2>/dev/null && sleep 2
/usr/bin/pkill -9 "Microsoft Excel" 2>/dev/null || true

if [[ -d "/Applications/Microsoft Excel.app" ]]; then
    APP_VERSION=$(defaults read "/Applications/Microsoft Excel.app/Contents/Info.plist" CFBundleVersion)
    echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
    if ! is-at-least 16.17 "${APP_VERSION}"; then
        APP_GENERATION="2016"
    fi
    if [[ "${APP_GENERATION}" == "2019" ]]; then
        if ! is-at-least 16.73 "${APP_VERSION}" && is-at-least 11.0.0 "${OS_VERSION}"; then
            echo "Office-Reset: The installed version of ${APP_NAME} (2019 generation) is ancient. Updating it now"
            RepairApp
        fi
        GetCustomManifestVersion
        if [[ -n "${CUSTOM_VERSION}" ]] && [[ "${APP_VERSION}" != "${CUSTOM_VERSION}" ]]; then
            echo "Office-Reset: ${APP_NAME} is ${APP_VERSION} on-disk, but the pinned version has been set to ${CUSTOM_VERSION}. Removing and reinstalling"
            /bin/rm -rf "/Applications/Microsoft Excel.app"
            RepairApp
        fi
    fi
    if [[ "${APP_GENERATION}" == "2016" ]]; then
        if ! is-at-least 16.16 "${APP_VERSION}"; then
            echo "Office-Reset: The installed version of ${APP_NAME} (2016 generation) is ancient. Updating it now"
            RepairApp
        fi
    fi

    echo "Office-Reset: Checking the app bundle for corruption"
    # Single invocation: capture both stdout and stderr; check $? from the assignment
    CODESIGN_RESULT=$(/usr/bin/codesign -vv --deep "/Applications/Microsoft Excel.app" 2>&1)
    if [[ $? -gt 0 ]]; then
        echo "Office-Reset: The ${APP_NAME} app bundle is damaged and reporting error: ${CODESIGN_RESULT}"
        if [[ "${CODESIGN_RESULT}" == *"OLE.framework"* ]]; then
            echo "Office-Reset: Only OLE.framework has been modified. Ignoring the repair"
        else
            echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled"
            /bin/rm -rf "/Applications/Microsoft Excel.app"
            RepairApp
        fi
    else
        echo "Office-Reset: Codesign passed successfully"
    fi
else
    echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -f /Library/Preferences/com.microsoft.Excel.plist
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Excel.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.Excel.plist"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Excel"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.Excel"

/bin/rm -rf "/Applications/.Microsoft Excel.app.installBackup"

/bin/rm -rf "/Library/Application Support/Microsoft/Office365/User Content.localized/Startup.localized/Excel"
# (N) glob qualifier: silently skips rm if no matching files exist (prevents "no matches found" errors)
/bin/rm -rf "/Library/Application Support/Microsoft/Office365/User Content.localized/Templates.localized/"*.xlt(N)
/bin/rm -rf "/Library/Application Support/Microsoft/Office365/User Content.localized/Templates.localized/"*.xltx(N)
/bin/rm -rf "/Library/Application Support/Microsoft/Office365/User Content.localized/Templates.localized/"*.xltm(N)
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/User Content.localized/Startup.localized/Excel"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/User Content.localized/Templates.localized/"*.xlt(N)
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/User Content.localized/Templates.localized/"*.xltx(N)
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/User Content.localized/Templates.localized/"*.xltm(N)
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/mip_policy"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/ComRPC32"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/TemporaryItems"
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg"

/usr/bin/security delete-certificate -c 'Microsoft.Office.Excel.ProtectedDataServices'

/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.Excel"

exit 0
