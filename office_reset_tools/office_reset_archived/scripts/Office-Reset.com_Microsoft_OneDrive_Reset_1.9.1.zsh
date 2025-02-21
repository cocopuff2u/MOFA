#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_OneDrive"
autoload is-at-least
APP_NAME="Microsoft OneDrive"
DOWNLOAD_URL="https://go.microsoft.com/fwlink/?linkid=823060"
OS_VERSION=$(sw_vers -productVersion)

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

/usr/bin/pkill -9 'OneDrive'
/usr/bin/pkill -9 'FinderSync'
/usr/bin/pkill -9 'OneDriveStandaloneUpdater'
/usr/bin/pkill -9 'OneDriveUpdater'

if [ -d "/Applications/OneDrive.app" ]; then
	APP_VERSION=$(defaults read /Applications/OneDrive.app/Contents/Info.plist CFBundleVersion)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 21083.0 $APP_VERSION && is-at-least 10.12 $OS_VERSION; then
		echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Updating it now"
		RepairApp
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	/usr/bin/codesign -vv --deep /Applications/OneDrive.app
	if [ $? -gt 0 ]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled" 
		/bin/rm -rf /Applications/OneDrive.app
		RepairApp
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
else
	echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -rf "$HOME/Library/Caches/OneDrive"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.OneDrive"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.OneDriveUpdater"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.OneDriveStandaloneUpdater"

/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveStandaloneUpdater.binarycookies"

/bin/rm -rf "$HOME/Library/WebKit/com.microsoft.OneDrive"

/bin/rm -rf "$HOME/Library/Containers/com.microsoft.OneDrive-mac"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.OneDrive.FinderSync"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.OneDrive-mac.FinderSync"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.OneDriveLauncher"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.OneDrive.FileProvider"

/bin/rm -rf "$HOME/Library/Logs/OneDrive"

/bin/rm -rf "$HOME/Library/Application Support/OneDrive"
/bin/rm -rf "$HOME/Library/Application Support/com.microsoft.OneDrive"
/bin/rm -rf "$HOME/Library/Application Support/com.microsoft.OneDriveUpdater"
/bin/rm -rf "$HOME/Library/Application Support/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -rf "$HOME/Library/Application Support/OneDriveUpdater"
/bin/rm -rf "$HOME/Library/Application Support/OneDriveStandaloneUpdater"

/bin/rm -rf "$HOME/Library/Application Scripts/com.microsoft.OneDrive.FinderSync"
/bin/rm -rf "$HOME/Library/Application Scripts/com.microsoft.OneDrive.FileProvider"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.OneDriveStandaloneSuite"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.OfficeOneDriveSyncIntegration"

/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.OfficeOneDriveSyncIntegration"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.OneDriveStandaloneSuite"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.OneDriveSyncClientSuite"

/bin/rm -f "$HOME/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.OneDriveUpdater.plist"
/bin/rm -f "$HOME/Library/Preferences/UBF8T346G9.OneDriveStandaloneSuite.plist"
/bin/rm -f "$HOME/Library/Preferences/UBF8T346G9.OfficeOneDriveSyncIntegration.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDriveUpdater.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDriveStandaloneUpdater.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDriveUpdater.plist"

/bin/rm -rf "$TMPDIR/com.microsoft.OneDrive"
/bin/rm -rf "$TMPDIR/com.microsoft.OneDrive.FinderSync"
/bin/rm -f "$TMPDIR/OneDriveVersion.xml"

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

echo "Display list-keychains for logged-in user"
/usr/bin/security list-keychains

/usr/bin/security delete-generic-password -l 'com.microsoft.OneDrive.FinderSync.HockeySDK'
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDrive.HockeySDK'
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDriveUpdater.HockeySDK'
/usr/bin/security delete-generic-password -l 'com.microsoft.OneDriveStandaloneUpdater.HockeySDK'
/usr/bin/security delete-generic-password -l 'OneDrive Standalone Cached Credential Business - Business1'
/usr/bin/security delete-generic-password -l 'OneDrive Standalone Cached Credential'

/usr/bin/security delete-generic-password -s 'OneAuthAccount'
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

exit 0