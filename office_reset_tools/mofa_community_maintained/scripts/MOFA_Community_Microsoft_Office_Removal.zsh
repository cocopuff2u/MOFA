#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Office_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removals the Microsoft Office suite for specific applications
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
#
# ============================================================


echo "Office-Reset: Starting preinstall for Remove_Office"
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

echo "Office-Reset: Stopping services"
/usr/bin/pkill -9 'Microsoft Word'
/usr/bin/pkill -9 'Microsoft Excel'
/usr/bin/pkill -9 'Microsoft PowerPoint'
/usr/bin/pkill -9 'Microsoft Outlook'
/usr/bin/pkill -9 'Microsoft OneNote'
/usr/bin/pkill -9 'OneDrive'
/usr/bin/pkill -9 'OneDrive Finder Integration'
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

/bin/launchctl stop /Library/LaunchAgents/com.microsoft.update.agent.plist
/bin/launchctl stop /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist
/bin/launchctl stop /Library/LaunchAgents/com.microsoft.OneDriveStandaloneUpdater.plist
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.autoupdate.helper
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.OneDriveUpdaterDaemon.plist
/bin/launchctl stop /Library/LaunchDaemons/com.microsoft.teams.TeamsUpdaterDaemon.plist

/bin/launchctl unload /Library/LaunchAgents/com.microsoft.update.agent.plist
/bin/launchctl unload /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist
/bin/launchctl unload /Library/LaunchAgents/com.microsoft.OneDriveStandaloneUpdater.plist
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.OneDriveUpdaterDaemon.plist
/bin/launchctl unload /Library/LaunchDaemons/com.microsoft.teams.TeamsUpdaterDaemon.plist

echo "Office-Reset: Removing apps"
/bin/rm -rf "/Applications/Microsoft Word.app"
/bin/rm -rf "/Applications/Microsoft Excel.app"
/bin/rm -rf "/Applications/Microsoft PowerPoint.app"
/bin/rm -rf "/Applications/Microsoft Outlook.app"
/bin/rm -rf "/Applications/Microsoft OneNote.app"
/bin/rm -rf "/Applications/OneDrive.app"
/bin/rm -rf "/Applications/Microsoft Teams.app"

echo "Office-Reset: Removing app data"
/bin/rm -rf "/Library/Application Support/Microsoft/MAU2.0"
/bin/rm -rf "/Library/Application Support/Microsoft/MERP2.0"
/bin/rm -rf "/Library/Application Support/Microsoft/Office365"
/bin/rm -rf "$HOME/Library/Application Support/Microsoft"
/bin/rm -rf "$HOME/Library/Application Scripts/com.microsoft.errorreporting"

/bin/rm -f "/Library/LaunchAgents/com.microsoft.update.agent.plist"
/bin/rm -f "/Library/LaunchAgents/com.microsoft.OneDriveStandaloneUpdater.plist"

/bin/rm -f "/Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist"
/bin/rm -f "/Library/LaunchDaemons/com.microsoft.office.licensingV2.helper.plist"
/bin/rm -f "/Library/LaunchDaemons/com.microsoft.OneDriveStandaloneUpdaterDaemon.plist"
/bin/rm -f "/Library/LaunchDaemons/com.microsoft.OneDriveUpdaterDaemon.plist"
/bin/rm -f "/Library/LaunchDaemons/com.microsoft.teams.TeamsUpdaterDaemon.plist"

/bin/rm -f "/Library/PrivilegedHelperTools/com.microsoft.autoupdate.helper"
/bin/rm -f "/Library/PrivilegedHelperTools/com.microsoft.autoupdate.helpertool"
/bin/rm -f "/Library/PrivilegedHelperTools/com.microsoft.office.licensingV2.helper"

/bin/rm -rf "/Library/Logs/Microsoft"

# OneDriveFolder=$(/bin/ls "$HOME" | grep 'OneDrive' --max-count=1)
# if [ "$OneDriveFolder" != "" ]; then
#	IsOneDrive=$(/usr/bin/xattr "$HOME/$OneDriveFolder" | grep 'com.apple.fileutil.SyncRootProviderRootContextList')
#	if [ "$IsOneDrive" = "com.apple.fileutil.SyncRootProviderRootContextList" ]; then
#		echo "Office-Reset: Removing OneDrive folder $OneDriveFolder"
#		/bin/rm -rf "$HOME/$OneDriveFolder"
#	fi
# fi

/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.Word.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.Excel.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.Powerpoint.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.Outlook.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.onenote.mac.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.OneDrive-mac.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.Word.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.Excel.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.Powerpoint.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.Outlook.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.onenote.mac.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDrive-mac.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Word.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Excel.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Powerpoint.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Outlook.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.onenote.mac.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDrive-mac.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.OneDrive.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.teams.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate2"
/bin/rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate.fba"
/bin/rm -rf "$HOME/Library/Caches/Microsoft"

/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.Office"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.ms"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.OfficeOsfWebHost"
/bin/rm -rf "$HOME/Library/Group Containers/group.com.microsoft"

echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

echo "Office-Reset: Removing package receipts"
/usr/sbin/pkgutil --forget com.microsoft.Word
/usr/sbin/pkgutil --forget com.microsoft.Excel
/usr/sbin/pkgutil --forget com.microsoft.Powerpoint
/usr/sbin/pkgutil --forget com.microsoft.Outlook
/usr/sbin/pkgutil --forget com.microsoft.onenote.mac
/usr/sbin/pkgutil --forget com.microsoft.OneDrive-mac

/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_Word.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_Excel.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_PowerPoint.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_Outlook.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_OneNote.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_AutoUpdate.app
/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_AU_Bootstrapper.app

/usr/sbin/pkgutil --forget com.microsoft.package.Proofing_Tools
/usr/sbin/pkgutil --forget com.microsoft.package.Fonts
/usr/sbin/pkgutil --forget com.microsoft.package.DFonts
/usr/sbin/pkgutil --forget com.microsoft.package.Frameworks

/usr/sbin/pkgutil --forget com.microsoft.pkg.licensing
/usr/sbin/pkgutil --forget com.microsoft.pkg.licensing.volume

/usr/sbin/pkgutil --forget com.microsoft.teams

/usr/sbin/pkgutil --forget com.microsoft.OneDrive

/bin/rm -f "/Library/Preferences/com.microsoft.office.licensingV2.backup"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate2.plist"

/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.OneDriveStandaloneUpdater.binarycookies"
/bin/rm -f "$HOME/Library/Cookies/com.microsoft.teams.binarycookies"

/bin/rm -rf "/Users/Shared/OnDemandInstaller"

exit 0