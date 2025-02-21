#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_SkypeForBusiness_Removal.zsh
# Repository: https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Removes the Microsoft Skype For Business application
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated for MOFA to continue maintenance where *Office-Reset.com* left off.
#
# ============================================================

echo "Office-Reset: Starting postinstall for Remove_SkypeForBusiness"
autoload is-at-least
SCRIPT_FOLDER=$(/usr/bin/dirname "$0")

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

/usr/bin/pkill -9 'Skype for Business'

/bin/rm -rf "$HOME/Library/Application Scripts/com.microsoft.SkypeForBusiness"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.SkypeForBusiness"
/bin/rm -rf "$HOME/Library/Preferences/com.microsoft.OutlookSkypeIntegration.plist"

/bin/rm -f "/Library/Preferences/com.microsoft.SkypeForBusiness.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.SkypeForBusiness.plist"
/bin/rm -f "$HOME/Library/Preferences/com.microsoft.SkypeForBusiness.plist"

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

/usr/bin/security delete-generic-password -l 'com.microsoft.SkypeForBusiness.HockeySDK'
/usr/bin/security delete-generic-password -l 'Skype for Business'

/bin/rm -rf "/Applications/Skype for Business.app"

/usr/sbin/pkgutil --forget com.microsoft.package.Microsoft_AU_Bootstrapper.app
/usr/sbin/pkgutil --forget com.microsoft.SkypeForBusiness

/usr/bin/sudo -u $LoggedInUser $SCRIPT_FOLDER/dockutil --remove com.microsoft.SkypeForBusiness

exit 0