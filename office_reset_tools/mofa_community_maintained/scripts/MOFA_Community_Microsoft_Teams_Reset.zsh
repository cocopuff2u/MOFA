#!/bin/zsh
# shellcheck shell=bash

# ============================================================
# Script Name: MOFA_Community_Microsoft_Teams_Reset.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets the Microsoft Teams
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.0.1 - @Theile additions to use shellcheck, define PATH, preserve Teams backgrounds, reset TCC. Classic Teams is dead.
#
# ============================================================

# Set PATH variable to SIP protected folders
export PATH=/usr/bin:/bin:/usr/sbin:/sbin

echo "Office-Reset: Starting Reset_Teams"
autoload is-at-least
APP_NAME="Microsoft Teams"
# DOWNLOAD_URL_TEAMS="https://go.microsoft.com/fwlink/?linkid=869428" # Old Classic URL pointing to same URL as the new
DOWNLOAD_URL_TEAMS="https://go.microsoft.com/fwlink/?linkid=2249065"
INSTALLATION_RETRIES=5
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
    LoggedInUserID=$(id -u "$LoggedInUser")
}

runAsUser() {
    launchctl asuser $LoggedInUserID sudo -u $LoggedInUser "$@"
}

RepairApp() {
	DOWNLOAD_URL="$1"
	DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
	if [ -d "$DOWNLOAD_FOLDER" ]; then
		rm -rf "$DOWNLOAD_FOLDER"
	fi
	mkdir -p "$DOWNLOAD_FOLDER"

	CDN_PKG_URL=$(/usr/bin/nscurl --location --head $DOWNLOAD_URL --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
	CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

	CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head $DOWNLOAD_URL --dump-header - | awk '/Content-Length:/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	CDN_PKG_MB=$((${CDN_PKG_SIZE} / 1024 / 1024))
	echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

	echo "Office-Reset: Starting ${APP_NAME} package download"
	/usr/bin/nscurl --background --download --large-download --location --download-directory $DOWNLOAD_FOLDER $DOWNLOAD_URL
	echo "Office-Reset: Finished package download"

	LOCAL_PKG_SIZE=$(cd "${DOWNLOAD_FOLDER}" && stat -qf%z "${CDN_PKG_NAME}")
	if [[ "${LOCAL_PKG_SIZE}" == "${CDN_PKG_SIZE}" || -z "${CDN_PKG_SIZE}" ]]; then
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

removeAncientTeamsVersion() {
	local ancientPath="${1}"
	echo "Office-Reset: Found ancient version of ${APP_NAME}: ${ancientPath}. Updating it now"
	/bin/rm -rf "${ancientPath}"
	RepairApp "$DOWNLOAD_URL_TEAMS"
	echo "Office-Reset: Checking the app bundle for corruption"
	appPath="/Applications/Microsoft Teams.app"
	/usr/bin/codesign -vv --deep "${appPath}"
	if [ $? -gt 0 ]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled" 
		/bin/rm -rf "${appPath}"
		RepairApp "$DOWNLOAD_URL_TEAMS"
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
}

FindEntryTeamsIdentity() {
	/usr/bin/security find-generic-password -l 'Microsoft Teams Identities Cache' 2> /dev/null 1> /dev/null
	echo $?
}

## MARK: Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser ($LoggedInUserID); Home Folder: $HOME"

/usr/bin/pkill -9 'Microsoft Teams*'

# Handle previous installation of Teams (if any)
appPath="/Applications/Microsoft Teams.app"
if [ -d "${appPath}" ]; then
	APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
	APP_BUNDLEID=$(defaults read "${appPath}/Contents/Info.plist" CFBundleIdentifier)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME} with bundle ID ${APP_BUNDLEID}"
	if ! is-at-least 23247.0 $APP_VERSION && is-at-least 10.15 $OS_VERSION; then
		echo "Office-Reset: The installed version of ${APP_NAME} is ancient. Removing it now"
		rm -rf "${appPath}"
	else
		echo "Office-Reset: The installed version of ${APP_NAME} is $APP_VERSION. Should be fine"
	fi
fi

appPath="/Applications/Microsoft Teams classic.app"
if [ -d "${appPath}" ]; then
	removeAncientTeamsVersion "${appPath}"
fi
appPath="/Applications/Microsoft Teams (work or school).app"
if [ -d "${appPath}" ]; then
	removeAncientTeamsVersion "${appPath}"
fi


# Move backgrounds for Teams Classic (dead)
backgroundsFolder="$HOME/Library/Application Support/Microsoft/Teams/Backgrounds"
if [ -d "${backgroundsFolder}" ]; then
	echo "Office-Reset: Detected Classic backgrounds for ${APP_NAME}"
	destFolder="$HOME/Teams_Old_Backgrounds"
	orgDestFolder="${destFolder}"
	folderCounter=0
	while [ -e "${destFolder}" ]; do
		((folderCounter++))
		destFolder="${orgDestFolder}${folderCounter}"
	done
	echo "Office-Reset: moved to ${destFolder}"
	mv "${backgroundsFolder}" "${destFolder}"
	open "${destFolder}"
fi
# Preserve backgrounds
backgroundsFolder="$HOME/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/Backgrounds"
if [ -d "${backgroundsFolder}" ]; then
	echo "Office-Reset: Preserve backgrounds for ${APP_NAME}"
	mv "${backgroundsFolder}" /tmp/
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -rf $HOME/Library/Application\ Support/Teams
/bin/rm -rf $HOME/Library/Application\ Support/Microsoft/Teams


/bin/rm -rf $HOME/Library/Application\ Support/com.microsoft.teams
/bin/rm -rf $HOME/Library/Application\ Support/com.microsoft.teams.helper

/bin/rm -rf $HOME/Library/Application\ Scripts/UBF8T346G9.com.microsoft.teams
/bin/rm -rf $HOME/Library/Application\ Scripts/com.microsoft.teams2
/bin/rm -rf $HOME/Library/Application\ Scripts/com.microsoft.teams2.launcher
/bin/rm -rf $HOME/Library/Application\ Scripts/com.microsoft.teams2.notificationcenter

/bin/rm -rf $HOME/Library/Caches/com.microsoft.teams
/bin/rm -rf $HOME/Library/Caches/com.microsoft.teams.helper
/bin/rm -f $HOME/Library/Cookies/com.microsoft.teams.binarycookies
/bin/rm -f $HOME/Library/HTTPStorages/com.microsoft.teams.binarycookies
/bin/rm -rf $HOME/Library/HTTPStorages/com.microsoft.teams
/bin/rm -rf $HOME/Library/Logs/Microsoft\ Teams
/bin/rm -rf $HOME/Library/Logs/Microsoft\ Teams\ Helper
/bin/rm -rf $HOME/Library/Logs/Microsoft\ Teams\ Helper \(Renderer\)
/bin/rm -rf $HOME/Library/Saved\ Application\ State/com.microsoft.teams.savedState
/bin/rm -rf $HOME/Library/WebKit/com.microsoft.teams

/bin/rm -rf $HOME/Library/Containers/com.microsoft.teams2
/bin/rm -rf $HOME/Library/Containers/com.microsoft.teams2.launcher
/bin/rm -rf $HOME/Library/Containers/com.microsoft.teams2.notificationcenter

/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.com.microsoft.teams
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.com.microsoft.oneauth

/bin/rm -rf /Library/Application\ Support/TeamsUpdaterDaemon
/bin/rm -rf /Library/Application\ Support/Microsoft/TeamsUpdaterDaemon
/bin/rm -rf /Library/Application\ Support/Teams

/bin/rm -f $HOME/Library/Preferences/com.microsoft.teams.plist
/bin/rm -f /Library/Managed\ Preferences/com.microsoft.teams.plist
/bin/rm -f /Library/Preferences/com.microsoft.teams.plist
/bin/rm -f $HOME/Library/Preferences/com.microsoft.teams.helper.plist
/bin/rm -f /Library/Managed\ Preferences/com.microsoft.teams.helper.plist
/bin/rm -f /Library/Preferences/com.microsoft.teams.helper.plist

/bin/rm -rf $TMPDIR/com.microsoft.teams
/bin/rm -rf $TMPDIR/com.microsoft.teams\ Crashes
/bin/rm -rf $TMPDIR/Teams
/bin/rm -rf $TMPDIR/Microsoft\ Teams\ Helper\ \(Renderer\)
/bin/rm -rf $TMPDIR/v8-compile-cache-501

/bin/rm -rf /Library/Logs/Microsoft/Teams

# Restore backgrounds
if [ -d "/tmp/Backgrounds" ] ; then
	echo "Office-Reset: Restore backgrounds for ${APP_NAME}"
	runAsUser mkdir -p "$HOME/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/"
	mv /tmp/Backgrounds "$HOME/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/"
	chown -R $LoggedInUser "$HOME/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams"
fi

# Reset TCC (PPPC) for Teams
echo "Reset TCC for com.microsoft.teams2"
tccutil reset com.microsoft.teams2

# Keychain items
KeychainHasLogin=$(runAsUser /usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	runAsUser /usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

echo "Display list-keychains for logged-in user"
runAsUser /usr/bin/security list-keychains

while [[ $(FindEntryTeamsIdentity) -eq 0 ]]; do
	runAsUser /usr/bin/security delete-generic-password -l 'Microsoft Teams Identities Cache'
done
runAsUser /usr/bin/security delete-generic-password -l 'Teams Safe Storage'
runAsUser /usr/bin/security delete-generic-password -l 'Microsoft Teams (work or school) Safe Storage'
runAsUser /usr/bin/security delete-generic-password -l 'teamsIv'
runAsUser /usr/bin/security delete-generic-password -l 'teamsKey'
runAsUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.HockeySDK'
runAsUser /usr/bin/security delete-generic-password -l 'com.microsoft.teams.helper.HockeySDK'


# Install Teams if damaged or not found
appPath="/Applications/Microsoft Teams.app"
if ! codesign -vv --deep "${appPath}"; then
	echo "Office-Reset: ${APP_NAME} is damaged or not existing so preparing for reinstallation"
	[ -e "${appPath}" ] && rm -rf "${appPath}"
else
	echo "Office-Reset: Codesign passed successfully"
	APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
	echo "Office-Reset: The installed version of ${APP_NAME} is $APP_VERSION"
fi
folderCounter=1
while [ ! -d "${appPath}" ]; do
	echo "Office-Reset: ${APP_NAME} not installed. Trying ${folderCounter}. installation at the most $INSTALLATION_RETRIES times, now"
	RepairApp "$DOWNLOAD_URL_TEAMS"
	codesign -vv --deep "${appPath}"
	if [ $? -gt 0 ]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed for reinstallation"
		[ -e "${appPath}" ] && rm -rf "${appPath}"
	else
		echo "Office-Reset: Codesign passed successfully"
		APP_VERSION=$(defaults read "${appPath}/Contents/Info.plist" CFBundleVersion)
		echo "Office-Reset: The installed version of ${APP_NAME} is now $APP_VERSION"
	fi
	[[ $folderCounter -ge $INSTALLATION_RETRIES ]] && break
	((folderCounter++))
done

exit 0
