#!/bin/zsh

echo "Office-Reset: Starting postinstall for Remove_Outlook_Data"
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

/usr/bin/pkill -9 'Microsoft Outlook'

/bin/rm -f "$HOME/Library/Preferences/com.microsoft.Outlook.plist"

/bin/rm -rf "$HOME/Library/Group Containers/UBF8T346G9.Office/Outlook"
/bin/rm -f "$HOME/Library/Group Containers/UBF8T346G9.Office/OutlookProfile.plist"

exit 0