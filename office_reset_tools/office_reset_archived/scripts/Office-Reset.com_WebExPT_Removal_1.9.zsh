#!/bin/zsh

echo "Office-Reset: Starting postinstall for Remove_WebExPT"
autoload is-at-least
APP_NAME="WebEx Productivity Tools"

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

echo "Office-Reset: Running native uninstall routine for ${APP_NAME}"
/Applications/WebEx\ Productivity\ Tools/Uninstall/Contents/MacOS/Uninstall

echo "Office-Reset: Stopping WebEx agent"
/bin/launchctl stop /Library/LaunchAgents/com.webex.pluginagent.plist
/bin/launchctl unload /Library/LaunchAgents/com.webex.pluginagent.plist

echo "Office-Reset: Removing agent configuration for ${APP_NAME}"
/bin/rm -rf "$HOME/Library/Application Support/Cisco/Webex Plugin"
/bin/rm -rf "$HOME/Library/Application Support/Cisco/Webex Meetings"
/bin/rm -rf "$HOME/Library/Caches/com.cisco.webex.pluginservice"
/bin/rm -rf "$HOME/Library/Caches/com.cisco.webex.webexmta"
/bin/rm -rf "$HOME/Library/Group Containers/group.com.cisco.webex.meetings"
/bin/rm -rf "$HOME/Library/Logs/PT"
/bin/rm -rf "$HOME/Library/Logs/webexmta"
/bin/rm -f "$HOME/Library/Preferences/com.cisco.webex.pluginservice.plist"

echo "Office-Reset: Removing binaries for ${APP_NAME}"
/bin/rm -rf "/Library/Application Support/Microsoft/WebExPlugin"
/bin/rm -rf "/Library/ScriptingAdditions/WebexScriptAddition.osax"
/bin/rm -rf "/Users/Shared/WebExPlugin"

/bin/rm -rf "/Applications/WebEx Productivity Tools"

/usr/sbin/pkgutil --forget olp.mac.webex.com

exit 0