#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_Teams"
autoload is-at-least
APP_NAME="Microsoft Teams"
DOWNLOAD_URL="https://go.microsoft.com/fwlink/?linkid=869428"
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

/usr/bin/pkill -9 'Microsoft Teams'
/usr/bin/pkill -9 'Microsoft Teams Helper'

if [ -d "/Applications/Microsoft Teams.app" ]; then
	APP_VERSION=$(defaults read /Applications/Microsoft\ Teams.app/Contents/Info.plist CFBundleVersion)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 517261.0 $APP_VERSION && is-at-least 10.11 $OS_VERSION; then
		echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Updating it now"
		RepairApp
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	/usr/bin/codesign -vv --deep /Applications/Microsoft\ Teams.app
	if [ $? -gt 0 ]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled" 
		/bin/rm -rf /Applications/Microsoft\ Teams.app
		RepairApp
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
else
	echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -rf "$HOME/Library/Application Support/Teams"
/bin/rm -rf "$HOME/Library/Application Support/Microsoft/Teams"
/bin/rm -rf "$HOME/Library/Application Support/com.microsoft.teams"
/bin/rm -rf "$HOME/Library/Application Support/com.microsoft.teams.helper"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.teams"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.teams.helper"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.teams.binarycookies"
/bin/rm -rf "$HOME/Library/Logs/Microsoft Teams"
/bin/rm -rf "$HOME/Library/Logs/Microsoft Teams Helper"
/bin/rm -rf "$HOME/Library/Logs/Microsoft Teams Helper (Renderer)"
/bin/rm -rf "$HOME/Library/Saved Application State/com.microsoft.teams.savedState"
/bin/rm -rf "$HOME/Library/WebKit/com.microsoft.teams"

/bin/rm -rf "/Library/Application Support/TeamsUpdaterDaemon"
/bin/rm -rf "/Library/Application Support/Microsoft/TeamsUpdaterDaemon"
/bin/rm -rf "/Library/Application Support/Teams"

/bin/rm -f "$HOME/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.teams.helper.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.teams.helper.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.teams.helper.plist"

/bin/rm -rf "$TMPDIR/com.microsoft.teams"
/bin/rm -rf "$TMPDIR/com.microsoft.teams Crashes"
/bin/rm -rf "$TMPDIR/Teams"
/bin/rm -rf "$TMPDIR/Microsoft Teams Helper (Renderer)"
/bin/rm -rf "$TMPDIR/v8-compile-cache-501"

KeychainHasLogin=$(/usr/bin/sudo -u $LoggedInUser /usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/sudo -u $LoggedInUser /usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

echo "Display list-keychains for logged-in user"
/usr/bin/sudo -u $LoggedInUser /usr/bin/security list-keychains

/usr/bin/sudo -u $LoggedInUser /usr/bin/security delete-generic-password -l 'Microsoft Teams Identities Cache'
/usr/bin/sudo -u $LoggedInUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.HockeySDK'
/usr/bin/sudo -u $LoggedInUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.helper.HockeySDK'

exit 0