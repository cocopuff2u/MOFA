#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_Factory"
autoload is-at-least

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

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Stopping apps and services"
/usr/bin/pkill -9 'Microsoft Word'
/usr/bin/pkill -9 'Microsoft Excel'
/usr/bin/pkill -9 'Microsoft PowerPoint'
/usr/bin/pkill -9 'Microsoft Outlook'
/usr/bin/pkill -9 'Microsoft OneNote'
/usr/bin/pkill -9 'OneDrive'
/usr/bin/pkill -9 'FinderSync'
/usr/bin/pkill -9 'OneDriveStandaloneUpdater'
/usr/bin/pkill -9 'OneDriveUpdater'
/usr/bin/pkill -9 'Microsoft Teams'
/usr/bin/pkill -9 'Microsoft Teams Helper'
/usr/bin/pkill -9 'Microsoft AutoUpdate'
/usr/bin/pkill -9 'Microsoft Update Assistant'
/usr/bin/pkill -9 'Microsoft AU Daemon'
/usr/bin/pkill -9 'Microsoft AU Bootstrapper'
/usr/bin/pkill -9 'com.microsoft.autoupdate.helper'
/usr/bin/pkill -9 'com.microsoft.autoupdate.helpertool'
/usr/bin/pkill -9 'com.microsoft.autoupdate.bootstrapper.helper'

echo "Office-Reset: Removing preferences and containers"
/bin/rm -rf "/Library/Logs/Microsoft/autoupdate.log"
/bin/rm -rf "/Library/Logs/Microsoft/InstallLogs"
/bin/rm -rf "/Library/Logs/Microsoft/Teams"
/bin/rm -rf "/Library/Logs/Microsoft/OneDrive"

/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.office.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -rf "$HOME/Library/Application Support/Microsoft"

/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate2"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate.fba"

/bin/rm -rf "/Library/Application Support/Microsoft/Office365"

/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.Office"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.ms"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.OfficeOsfWebHost"

/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.com.microsoft.oneauth"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.Office"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.ms"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.OfficeOsfWebHost"
/bin/rm -rf "$HOME/Library/Application Scripts/UBF8T346G9.OfficeOneDriveSyncIntegration"

/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveStandaloneUpdater.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.teams.binarycookies"

/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba"
/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2"
/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.OneDrive"
/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -rf "$HOME/Library/HTTPStorages/com.microsoft.teams"

/bin/rm -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba.binarycookies"
/bin/rm -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2.binarycookies"
/bin/rm -f "$HOME/Library/HTTPStorages/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "$HOME/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater.binarycookies"
/bin/rm -f "$HOME/Library/HTTPStorages/com.microsoft.teams.binarycookies"

/bin/rm -rf "$HOME/Library/Containers/com.microsoft.errorreporting"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.netlib.shipassertprocess"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.Office365ServiceV2"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.RMS-XPCService"

exit 0