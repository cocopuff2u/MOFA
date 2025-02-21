#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_AutoUpdate"
autoload is-at-least
APP_NAME="Microsoft AutoUpdate"
DOWNLOAD_URL="https://go.microsoft.com/fwlink/?linkid=830196"

GetLoggedInUser() {
	LOGGEDIN=$(/bin/echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/Name :/&&!/loginwindow/{print $3}')
	if [ "$LOGGEDIN" = "" ]; then
		echo "$USER"
	else
		echo "$LOGGEDIN"
	fi
}

SetHomeFolder() {
	HOME=$(dscl . read /Users/"$1" NFSHomeDirectory | cut -d ':' -f2 | cut -d ' ' -f2)
	if [ "$HOME" = "" ]; then
		if [ -d "/Users/$1" ]; then
			HOME="/Users/$1"
		else
			HOME=$(eval echo "~$1")
		fi
	fi
}

RepairApp() {
	DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
	if [ -d "$DOWNLOAD_FOLDER" ]; then
		rm -rf "$DOWNLOAD_FOLDER"
	fi
	mkdir -p "$DOWNLOAD_FOLDER"

	CDN_PKG_URL=$(/usr/bin/nscurl --location --head $DOWNLOAD_URL --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
	CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

	CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head $DOWNLOAD_URL --dump-header - | awk '/Content-Length/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	CDN_PKG_MB=$(/bin/expr ${CDN_PKG_SIZE} / 1000 / 1000)
	echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

	echo "Office-Reset: Starting ${APP_NAME} package download"
	/usr/bin/nscurl --background --download --large-download --location --download-directory $DOWNLOAD_FOLDER $DOWNLOAD_URL
	echo "Office-Reset: Finished package download"

	LOCAL_PKG_SIZE=$(cd "${DOWNLOAD_FOLDER}" && stat -qf%z "${CDN_PKG_NAME}")
	if [[ "${LOCAL_PKG_SIZE}" == "${CDN_PKG_SIZE}" ]]; then
		echo "Office-Reset: Downloaded package is wholesome"
	else
		echo "Office-Reset: Downloaded package is malformed. Local file size: ${LOCAL_PKG_SIZE}"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		exit 0
	fi

	LOCAL_PKG_SIGNING=$(/usr/sbin/pkgutil --check-signature ${DOWNLOAD_FOLDER}${CDN_PKG_NAME} | awk '/Developer ID Installer'/ | cut -d ':' -f 2 | awk '{$1=$1};1')
	if [[ "${LOCAL_PKG_SIGNING}" == "Microsoft Corporation (UBF8T346G9)" ]]; then
		echo "Office-Reset: Downloaded package is signed by Microsoft"
	else
		echo "Office-Reset: Downloaded package is not signed by Microsoft"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		exit 0
	fi

	echo "Office-Reset: Starting package install"
	sudo /usr/sbin/installer -pkg ${DOWNLOAD_FOLDER}${CDN_PKG_NAME} -target /
	if [ $? -eq 0 ]; then
		echo "Office-Reset: Package installed successfully"
	else
		echo "Office-Reset: Package installation failed"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		exit 0
	fi
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Stopping update services"
/usr/bin/pkill -9 'Microsoft AutoUpdate'
/usr/bin/pkill -9 'Microsoft Update Assistant'
/usr/bin/pkill -9 'Microsoft AU Daemon'
/usr/bin/pkill -9 'Microsoft AU Bootstrapper'
/usr/bin/pkill -9 'com.microsoft.autoupdate.helper'
/usr/bin/pkill -9 'com.microsoft.autoupdate.helpertool'
/usr/bin/pkill -9 'com.microsoft.autoupdate.bootstrapper.helper'

/bin/launchctl stop /Library/LaunchAgents/com.microsoft.update.agent.plist
/bin/launchctl stop /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.autoupdate.helper
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist

/bin/launchctl unload /Library/LaunchAgents/com.microsoft.update.agent.plist
/bin/launchctl unload /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate2"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate.fba"

/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2"
/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba"

/bin/rm -rf "$HOME/Library/Application Support/Microsoft AU Daemon"

/bin/rm -rf "/Library/Application Support/Microsoft/MERP2.0"

/bin/rm -rf "$TMPDIR/MSauClones"
/bin/rm -rf "/Library/Caches/com.microsoft.autoupdate.helper/"
/bin/rm -rf "/Library/Caches/com.microsoft.autoupdate.fba/"
/bin/rm -f "$TMPDIR/TelemetryUploadFilecom.microsoft.autoupdate.fba.txt"
/bin/rm -f "$TMPDIR/TelemetryUploadFilecom.microsoft.autoupdate2.txt"

/bin/rm -rf "/Applications/.Microsoft Word.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft Excel.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft PowerPoint.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft Outlook.app.installBackup"
/bin/rm -rf "/Applications/.Microsoft OneNote.app.installBackup"

/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 AcknowledgedDataCollectionPolicy -string 'RequiredDataOnly'

if [ -d "/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app" ]; then
	APP_VERSION=$(defaults read /Library/Application\ Support/Microsoft/MAU2.0/Microsoft\ AutoUpdate.app/Contents/Info.plist CFBundleVersion)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 4.49 $APP_VERSION; then
		echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Updating it now"
		RepairApp
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	/usr/bin/codesign -vv --deep /Library/Application\ Support/Microsoft/MAU2.0/Microsoft\ AutoUpdate.app
	if [ $? -gt 0 ]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled" 
		/bin/rm -rf /Library/Application\ Support/Microsoft/MAU2.0/Microsoft\ AutoUpdate.app
		RepairApp
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
else
	echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Creating new preferences"
/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app" "{ 'Application ID' = 'MSau04'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"

WORD_VERSION=$(defaults read /Applications/Microsoft\ Word.app/Contents/Info.plist CFBundleVersion)
if [[ "${WORD_VERSION}" != "" ]]; then
	if is-at-least 16.17 $WORD_VERSION; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Word.app" "{ 'Application ID' = 'MSWD2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Word.app" "{ 'Application ID' = 'MSWD15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

EXCEL_VERSION=$(defaults read /Applications/Microsoft\ Excel.app/Contents/Info.plist CFBundleVersion)
if [[ "${EXCEL_VERSION}" != "" ]]; then
	if is-at-least 16.17 $EXCEL_VERSION; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Excel.app" "{ 'Application ID' = 'XCEL2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Excel.app" "{ 'Application ID' = 'XCEL15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

POWERPOINT_VERSION=$(defaults read /Applications/Microsoft\ PowerPoint.app/Contents/Info.plist CFBundleVersion)
if [[ "${POWERPOINT_VERSION}" != "" ]]; then
	if is-at-least 16.17 $POWERPOINT_VERSION; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft PowerPoint.app" "{ 'Application ID' = 'PPT32019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft PowerPoint.app" "{ 'Application ID' = 'PPT315'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

OUTLOOK_VERSION=$(defaults read /Applications/Microsoft\ Outlook.app/Contents/Info.plist CFBundleVersion)
if [[ "${OUTLOOK_VERSION}" != "" ]]; then
	if is-at-least 16.17 $OUTLOOK_VERSION; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Outlook.app" "{ 'Application ID' = 'OPIM2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Outlook.app" "{ 'Application ID' = 'OPIM15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

ONENOTE_VERSION=$(defaults read /Applications/Microsoft\ OneNote.app/Contents/Info.plist CFBundleVersion)
if [[ "${ONENOTE_VERSION}" != "" ]]; then
	if is-at-least 16.17 $ONENOTE_VERSION; then
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft OneNote.app" "{ 'Application ID' = 'ONMC2019'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	else
		/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft OneNote.app" "{ 'Application ID' = 'ONMC15'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
	fi
fi

if [ -d "/Applications/OneDrive.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/OneDrive.app" "{ 'Application ID' = 'ONDR18'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
fi

if [ -d "/Applications/Microsoft Teams.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Teams.app" "{ 'Application ID' = 'TEAMS10'; LCID = 1033 ; 'App Domain' = 'com.microsoft.office' ; }"
fi

if [ -d "/Applications/Microsoft Edge.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Edge.app" "{ 'Application ID' = 'EDGE01'; LCID = 1033 ; }"
fi
if [ -d "/Applications/Microsoft Edge Beta.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Edge Beta.app" "{ 'Application ID' = 'EDBT01'; LCID = 1033 ; }"
fi
if [ -d "/Applications/Microsoft Edge Canary.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Edge Canary.app" "{ 'Application ID' = 'EDCN01'; LCID = 1033 ; }"
fi
if [ -d "/Applications/Microsoft Edge Dev.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Edge Dev.app" "{ 'Application ID' = 'EDDV01'; LCID = 1033 ; }"
fi

if [ -d "/Applications/Microsoft Remote Desktop.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Remote Desktop.app" "{ 'Application ID' = 'MSRD10'; LCID = 1033 ; }"
fi

if [ -d "/Applications/Skype For Business.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Skype For Business.app" "{ 'Application ID' = 'MSFB16'; LCID = 1033 ; }"
fi

if [ -d "/Applications/Company Portal.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Company Portal.app" "{ 'Application ID' = 'IMCP01'; LCID = 1033 ; }"
fi

if [ -d "/Applications/Microsoft Defender ATP.app" ]; then
	/usr/bin/defaults write /Library/Preferences/com.microsoft.autoupdate2 ApplicationsSystem -dict-add "/Applications/Microsoft Defender ATP.app" "{ 'Application ID' = 'WDAV00'; LCID = 1033 ; }"
fi

exit 0