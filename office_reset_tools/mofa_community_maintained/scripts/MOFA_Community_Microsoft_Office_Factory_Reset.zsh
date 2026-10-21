#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Office_Factory_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets the Microsoft Office suite for specific applications
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          - Replaced eval in SetHomeFolder with safe dscl/path fallback
#          - Removed unused autoload is-at-least
#          - Replaced 19 individual pkill -9 calls with a SIGTERM → sleep → SIGKILL
#            pattern over a single named array; 2>/dev/null || true on all calls
#          - Changed rm -rf on autoupdate.log (a file) to rm -f
#          - All [ ] / = "" → [[ ]] / -z throughout
# ============================================================


echo "Office-Reset: Starting postinstall for Reset_Factory"

GetLoggedInUser() {
	LOGGEDIN=$(/bin/echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/Name /&&!/loginwindow/{print $3}')
	if [[ -z "$LOGGEDIN" ]]; then
		echo "$USER"
	else
		echo "$LOGGEDIN"
	fi
}

SetHomeFolder() {
	# Use dscl to resolve home directory; fall back to /Users/<username>
	HOME=$(dscl . -read "/Users/$1" NFSHomeDirectory 2>/dev/null | sed -n 's/^NFSHomeDirectory: //p')
	if [[ -z "$HOME" ]]; then
		HOME="/Users/$1"
	fi
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

# ---------------------------------------------------------------------------
# Stop all Microsoft processes
# SIGTERM first for a graceful quit attempt; SIGKILL after 3 seconds for any
# that did not respond. 2>/dev/null || true suppresses "no matching processes"
# noise in Jamf logs.
# ---------------------------------------------------------------------------
echo "Office-Reset: Stopping apps and services"

MS_PROCESSES=(
	"Microsoft Word"
	"Microsoft Excel"
	"Microsoft PowerPoint"
	"Microsoft Outlook"
	"Microsoft OneNote"
	"OneDrive"
	"FinderSync"
	"OneDriveStandaloneUpdater"
	"OneDriveUpdater"
	"Microsoft Teams"
	"Microsoft Teams Helper"
	"Microsoft AutoUpdate"
	"Microsoft Update Assistant"
	"Microsoft AU Daemon"
	"Microsoft AU Bootstrapper"
	"com.microsoft.autoupdate.helper"
	"com.microsoft.autoupdate.helpertool"
	"com.microsoft.autoupdate.bootstrapper.helper"
)

for proc in "${MS_PROCESSES[@]}"; do
	/usr/bin/pkill "$proc" 2>/dev/null || true
done
sleep 3
for proc in "${MS_PROCESSES[@]}"; do
	/usr/bin/pkill -9 "$proc" 2>/dev/null || true
done

# ---------------------------------------------------------------------------
# Remove logs, preferences, caches, containers, and support data
# ---------------------------------------------------------------------------
echo "Office-Reset: Removing preferences and containers"

/bin/rm -f  "/Library/Logs/Microsoft/autoupdate.log"   # file, not a directory
/bin/rm -rf "/Library/Logs/Microsoft/InstallLogs"
/bin/rm -rf "/Library/Logs/Microsoft/Teams"
/bin/rm -rf "/Library/Logs/Microsoft/OneDrive"

/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.autoupdate.fba.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.office.plist"
/bin/rm -f "/Library/Preferences/com.microsoft.teams.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.shared.plist"
/bin/rm -f "/Library/Managed Preferences/com.microsoft.office.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate2.plist"
/bin/rm -f "/var/root/Library/Preferences/com.microsoft.autoupdate.fba.plist"

/bin/rm -rf "${HOME}/Library/Application Support/Microsoft"

/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.autoupdate2"
/bin/rm -rf "${HOME}/Library/Caches/com.microsoft.autoupdate.fba"

/bin/rm -rf "/Library/Application Support/Microsoft/Office365"

/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.ms"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.OfficeOsfWebHost"

/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.com.microsoft.oneauth"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.Office"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.ms"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.OfficeOsfWebHost"
/bin/rm -rf "${HOME}/Library/Application Scripts/UBF8T346G9.OfficeOneDriveSyncIntegration"

/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDriveUpdater.binarycookies"
/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.OneDriveStandaloneUpdater.binarycookies"
/bin/rm -f "${HOME}/Library/Cookies/com.microsoft.teams.binarycookies"

/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate.fba"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate2"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.OneDrive"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater"
/bin/rm -rf "${HOME}/Library/HTTPStorages/com.microsoft.teams"

/bin/rm -f "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate.fba.binarycookies"
/bin/rm -f "${HOME}/Library/HTTPStorages/com.microsoft.autoupdate2.binarycookies"
/bin/rm -f "${HOME}/Library/HTTPStorages/com.microsoft.OneDrive.binarycookies"
/bin/rm -f "${HOME}/Library/HTTPStorages/com.microsoft.OneDriveStandaloneUpdater.binarycookies"
/bin/rm -f "${HOME}/Library/HTTPStorages/com.microsoft.teams.binarycookies"

/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.errorreporting"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.netlib.shipassertprocess"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Office365ServiceV2"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.RMS-XPCService"

exit 0
