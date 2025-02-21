#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_Credentials"
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

echo "Office-Reset: Quitting all apps gracefully"
/usr/bin/pkill -HUP 'Microsoft Word'
/usr/bin/pkill -HUP 'Microsoft Excel'
/usr/bin/pkill -HUP 'Microsoft PowerPoint'
/usr/bin/pkill -HUP 'Microsoft Outlook'
/usr/bin/pkill -HUP 'Microsoft OneNote'

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

echo "Display list-keychains for logged-in user"
/usr/bin/security list-keychains

echo "Office-Reset: Removing keychain entries"
/usr/bin/security delete-generic-password -s 'OneAuthAccount'

/usr/bin/security delete-internet-password -s 'msoCredentialSchemeADAL'
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeLiveId'
/usr/bin/security delete-generic-password -G 'MSOpenTech.ADAL.1'
/usr/bin/security delete-generic-password -G 'MSOpenTech.ADAL.1'
/usr/bin/security delete-generic-password -G 'MSOpenTech.ADAL.1'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 2'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 3'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 2'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 3'
/usr/bin/security delete-generic-password -l 'Microsoft Office Ticket Cache'
/usr/bin/security delete-generic-password -l 'com.microsoft.adalcache'
/usr/bin/security delete-generic-password -G 'Microsoft Office Data'
/usr/bin/security delete-generic-password -G 'Microsoft Office Data'
/usr/bin/security delete-generic-password -G 'Microsoft Office Data'
/usr/bin/security delete-generic-password -l 'com.microsoft.OutlookCore.Secret'

/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook'
/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook'
/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook'
/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook'

/usr/bin/security delete-generic-password -l 'MicrosoftOfficeRMSCredential'
/usr/bin/security delete-generic-password -l 'MicrosoftOfficeRMSCredential'
/usr/bin/security delete-generic-password -l 'MSProtection.framework.service'
/usr/bin/security delete-generic-password -l 'MSProtection.framework.service'

/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'
/usr/bin/security delete-generic-password -l 'Exchange'

echo "Office-Reset: Removing credential and license files"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.Office/mip_policy"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/DRM_Evo.plist"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.com.microsoft.oneauth"

/bin/rm -f "/Library/Preferences/com.microsoft.office.licensingV2.plist.bak"
/bin/mv /Library/Preferences/com.microsoft.office.licensingV2.plist /Library/Preferences/com.microsoft.office.licensingV2.backup

/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365.plist"
/bin/rm -f "/Library/Application Support/Microsoft/Office365/com.microsoft.Office365V2.plist"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365.plist"
/bin/mv "$HOME/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365V2.plist" "$HOME/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365V2.backup"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/com.microsoft.e0E2OUQxNUY1LTAxOUQtNDQwNS04QkJELTAxQTI5M0JBOTk4O.plist"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/e0E2OUQxNUY1LTAxOUQtNDQwNS04QkJELTAxQTI5M0JBOTk4O"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/com.microsoft.O4kTOBJ0M5ITQxATLEJkQ40SNwQDNtQUOxATL1YUNxQUO2E0e.plist"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/O4kTOBJ0M5ITQxATLEJkQ40SNwQDNtQUOxATL1YUNxQUO2E0e"

/bin/rm -rf "/Library/Microsoft/Office/Licenses"
/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.Office/Licenses"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.RMS-XPCService"
/bin/rm -rf "$HOME/Library/Application Scripts/com.microsoft.Office365ServiceV2"

/bin/rm -rf "$HOME/Library/Containers/com.microsoft.Word/Data/Library/Application Support/Microsoft"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.Excel/Data/Library/Application Support/Microsoft"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.Powerpoint/Data/Library/Application Support/Microsoft"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.Outlook/Data/Library/Application Support/Microsoft"
/bin/rm -rf "$HOME/Library/Containers/com.microsoft.onenote.mac/Data/Library/Application Support/Microsoft"

echo "Office-Reset: Changing preferences"
if [ -e "$HOME/Library/Preferences/com.microsoft.office.plist" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults delete $HOME/Library/Preferences/com.microsoft.office OfficeActivationEmailAddress
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Preferences/com.microsoft.office OfficeAutoSignIn -bool TRUE
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Preferences/com.microsoft.office HasUserSeenFREDialog -bool TRUE
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Preferences/com.microsoft.office HasUserSeenEnterpriseFREDialog -bool TRUE
fi
if [ -d "$HOME/Library/Containers/com.microsoft.Word/Data/Library/Preferences" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Containers/com.microsoft.Word/Data/Library/Preferences/com.microsoft.Word kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [ -d "$HOME/Library/Containers/com.microsoft.Excel/Data/Library/Preferences" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Containers/com.microsoft.Excel/Data/Library/Preferences/com.microsoft.Excel kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [ -d "$HOME/Library/Containers/com.microsoft.Powerpoint/Data/Library/Preferences" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Containers/com.microsoft.Powerpoint/Data/Library/Preferences/com.microsoft.Powerpoint kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [ -d "$HOME/Library/Containers/com.microsoft.Outlook/Data/Library/Preferences" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Containers/com.microsoft.Outlook/Data/Library/Preferences/com.microsoft.Outlook kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi
if [ -d "$HOME/Library/Containers/com.microsoft.onenote.mac/Data/Library/Preferences" ]; then
	/usr/bin/sudo -u $LoggedInUser /usr/bin/defaults write $HOME/Library/Containers/com.microsoft.onenote.mac/Data/Library/Preferences/com.microsoft.onenote.mac kSubUIAppCompletedFirstRunSetup1507 -bool FALSE
fi

/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg"

/usr/bin/killall cfprefsd

exit 0