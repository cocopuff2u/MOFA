#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_AutoUpdate_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets Microsoft AutoUpdate
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          - Replaced eval in SetHomeFolder with safe dscl/path fallback
#          - Removed unused OS_VERSION variable
#          - Introduced MAU_APP_PATH variable to eliminate repeated hard-coded paths
#          - Fixed launchctl stop to use service labels instead of plist paths
#          - Added 2>/dev/null || true to all launchctl stop/unload calls
#          - Removed redundant sudo from installer call (script runs as root)
#          - Fixed unquoted variable expansions throughout RepairApp
#          - Fixed CDN_PKG_SIZE / download to use resolved CDN_PKG_URL (not DOWNLOAD_URL)
#          - Replaced /bin/expr with native zsh arithmetic
#          - Removed unnecessary cd subshell in stat call
#          - Fixed pkgutil awk ambiguous quoting
#          - Changed failure exit 0 → exit 1 in RepairApp
#          - Captured codesign stderr for accurate error logging
#          - Added 2>/dev/null to all defaults read calls (suppresses noise when app absent)
#          - Quoted all app bundle paths (defaults read, defaults write, codesign, rm)
#          - Send SIGTERM before SIGKILL when stopping MAU processes
#          - Changed all [ ] / = "" / != "" → [[ ]] / -z / -n
#          - Quoted is-at-least arguments
# ============================================================

echo "Office-Reset: Starting postinstall for Reset_AutoUpdate"
autoload is-at-least
APP_NAME="Microsoft AutoUpdate"
DOWNLOAD_URL="https://go.microsoft.com/fwlink/?linkid=830196"
MAU_APP_PATH="/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app"

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
	HOME=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | awk '{print $NF}')
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

	CDN_PKG_URL=$(/usr/bin/nscurl --location --head "${DOWNLOAD_URL}" --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
	CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

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
	# Note: RepairApp intentionally returns (does not exit) so the
	# ApplicationsSystem registry rebuild below always runs after a repair.
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Stopping update services"
# Send SIGTERM first for graceful quit, then SIGKILL if still running.
# pkill uses regex; these patterns match all MAU process names as substrings.
/usr/bin/pkill "Microsoft AutoUpdate"          2>/dev/null; sleep 1
/usr/bin/pkill "Microsoft Update Assistant"    2>/dev/null
/usr/bin/pkill "Microsoft AU Daemon"           2>/dev/null
/usr/bin/pkill "Microsoft AU Bootstrapper"     2>/dev/null
/usr/bin/pkill "com.microsoft.autoupdate"      2>/dev/null
sleep 2
/usr/bin/pkill -9 "Microsoft AutoUpdate"          2>/dev/null || true
/usr/bin/pkill -9 "Microsoft Update Assistant"    2>/dev/null || true
/usr/bin/pkill -9 "Microsoft AU Daemon"           2>/dev/null || true
/usr/bin/pkill -9 "Microsoft AU Bootstrapper"     2>/dev/null || true
/usr/bin/pkill -9 "com.microsoft.autoupdate"      2>/dev/null || true

# launchctl stop requires the service label, not the plist path.
# launchctl unload takes the plist path (legacy interface, still functional).
/bin/launchctl stop  com.microsoft.update.agent          2>/dev/null || true
/bin/launchctl stop  com.microsoft.autoupdate.helper     2>/dev/null || true
/bin/launchctl unload /Library/LaunchAgents/com.microsoft.update.agent.plist          2>/dev/null || true
/bin/launchctl unload /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist     2>/dev/null || true
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper          2>/dev/null || true
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist    2>/dev/null || true

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -f  "${HOME}/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f  "${HOME}/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -f  "/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f  "/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -f  "/var/root/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f  "/var/root/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.autoupdate2"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.autoupdate.fba"

/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate2"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate.fba"

/bin/rm -rf "${HOME}/Library/Application Support/Microsoft AU Daemon"

/bin/rm -rf "/Library/Application Support/Microsoft/MERP2.0"

/bin/rm -rf "${TMPDIR}MSauClones"
/bin/rm -rf "/Library/Caches/com.microsoft.autoupdate.helper/"
/bin/rm -rf "/Library/Caches/com.microsoft.autoupdate.fba/"
/bin/rm -f  "${TMPDIR}TelemetryUploadFilecom.microsoft.autoupdate.fba.txt"
/bin/rm -f  "${TMPDIR}TelemetryUploadFilecom.microsoft.autoupdate2.txt"

/bin/rm -rf "/Applications/.Microsoft Word.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft Excel.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft PowerPoint.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft Outlook.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft OneNote.app.installBackup"

/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 \
	AcknowledgedDataCollectionPolicy -string 'RequiredDataOnly'

if [[ -d "${MAU_APP_PATH}" ]]; then
	APP_VERSION=$(defaults read "${MAU_APP_PATH}/Contents/Info.plist" CFBundleVersion 2>/dev/null)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 4.49 "${APP_VERSION}"; then
		echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Updating it now"
		RepairApp
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	CODESIGN_RESULT=$(/usr/bin/codesign -vv --deep "${MAU_APP_PATH}" 2>&1)
	if [[ $? -gt 0 ]]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled"
		echo "Office-Reset: Codesign error: ${CODESIGN_RESULT}"
		/bin/rm -rf "${MAU_APP_PATH}"
		RepairApp
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
else
	echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Creating new preferences"
/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
	-dict-add "${MAU_APP_PATH}" "{ 'Application ID' = 'MSau04'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"

WORD_VERSION=$(defaults read "/Applications/Microsoft Word.app/Contents/Info.plist" CFBundleVersion 2>/dev/null)
if [[ -n "${WORD_VERSION}" ]]; then
	if is-at-least 16.17 "${WORD_VERSION}"; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Word.app" "{ 'Application ID' = 'MSWD2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Word.app" "{ 'Application ID' = 'MSWD15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

EXCEL_VERSION=$(defaults read "/Applications/Microsoft Excel.app/Contents/Info.plist" CFBundleVersion 2>/dev/null)
if [[ -n "${EXCEL_VERSION}" ]]; then
	if is-at-least 16.17 "${EXCEL_VERSION}"; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Excel.app" "{ 'Application ID' = 'XCEL2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Excel.app" "{ 'Application ID' = 'XCEL15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

POWERPOINT_VERSION=$(defaults read "/Applications/Microsoft PowerPoint.app/Contents/Info.plist" CFBundleVersion 2>/dev/null)
if [[ -n "${POWERPOINT_VERSION}" ]]; then
	if is-at-least 16.17 "${POWERPOINT_VERSION}"; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft PowerPoint.app" "{ 'Application ID' = 'PPT32019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft PowerPoint.app" "{ 'Application ID' = 'PPT315'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

OUTLOOK_VERSION=$(defaults read "/Applications/Microsoft Outlook.app/Contents/Info.plist" CFBundleVersion 2>/dev/null)
if [[ -n "${OUTLOOK_VERSION}" ]]; then
	if is-at-least 16.17 "${OUTLOOK_VERSION}"; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Outlook.app" "{ 'Application ID' = 'OPIM2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft Outlook.app" "{ 'Application ID' = 'OPIM15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

ONENOTE_VERSION=$(defaults read "/Applications/Microsoft OneNote.app/Contents/Info.plist" CFBundleVersion 2>/dev/null)
if [[ -n "${ONENOTE_VERSION}" ]]; then
	if is-at-least 16.17 "${ONENOTE_VERSION}"; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft OneNote.app" "{ 'Application ID' = 'ONMC2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
			-dict-add "/Applications/Microsoft OneNote.app" "{ 'Application ID' = 'ONMC15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

if [[ -d "/Applications/OneDrive.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/OneDrive.app" "{ 'Application ID' = 'ONDR18'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
fi

if [[ -d "/Applications/Microsoft Teams.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Teams.app" "{ 'Application ID' = 'TEAMS10'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
fi

if [[ -d "/Applications/Microsoft Edge.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Edge.app" "{ 'Application ID' = 'EDGE01'; LCID = 1033 ; }"
fi
if [[ -d "/Applications/Microsoft Edge Beta.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Edge Beta.app" "{ 'Application ID' = 'EDBT01'; LCID = 1033 ; }"
fi
if [[ -d "/Applications/Microsoft Edge Canary.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Edge Canary.app" "{ 'Application ID' = 'EDCN01'; LCID = 1033 ; }"
fi
if [[ -d "/Applications/Microsoft Edge Dev.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Edge Dev.app" "{ 'Application ID' = 'EDDV01'; LCID = 1033 ; }"
fi

if [[ -d "/Applications/Microsoft Remote Desktop.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Remote Desktop.app" "{ 'Application ID' = 'MSRD10'; LCID = 1033 ; }"
fi

if [[ -d "/Applications/Skype For Business.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Skype For Business.app" "{ 'Application ID' = 'MSFB16'; LCID = 1033 ; }"
fi

if [[ -d "/Applications/Company Portal.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Company Portal.app" "{ 'Application ID' = 'IMCP01'; LCID = 1033 ; }"
fi

if [[ -d "/Applications/Microsoft Defender ATP.app" ]]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem \
		-dict-add "/Applications/Microsoft Defender ATP.app" "{ 'Application ID' = 'WDAV00'; LCID = 1033 ; }"
fi

exit 0
