#!/bin/zsh

# ============================================================
# Script Name: MOFA_Community_Microsoft_Outlook_Reset.zsh
# Repository:  https://github.com/cocopuff2u/MOFA/tree/main/office_reset_tools/mofa_community_maintained
# Description: Resets Microsoft Outlook
#
# Version History:
# 1.0.0 - Based on the latest available package from *Office-Reset.com*; recreated
#          for MOFA to continue maintenance where *Office-Reset.com* left off.
# 1.1.0 - Code review and hardening:
#          - Replaced eval in SetHomeFolder with safe dscl/path fallback
#          - Removed redundant sudo from installer call (script runs as root)
#          - Fixed unquoted variable expansions throughout (word-splitting / globbing)
#          - Combined double codesign call into single captured run (stderr included)
#          - Replaced /bin/expr with native zsh arithmetic
#          - Removed unnecessary cd subshell in stat call
#          - Initialized CUSTOM_VERSION / FULL_UPDATER at top of GetCustomManifestVersion
#          - Consolidated five FindEntry* functions into single FindKeychainEntry helper
#          - Quoted $status in HandleSecurityDeleteResult calls
#          - Fixed OfficeAclFiles glob: quoted HOME prefix, removed backslash-escaped spaces
#          - Send SIGTERM before SIGKILL when quitting Outlook
#          - Quoted all app bundle, system library, and $HOME paths
#          - Minor: -z / -n tests in place of = "" comparisons; [[ ]] throughout
# 1.1.1 - Security (GHSA-gw3c-6fvh-7gqm): download to a root-private mktemp folder instead of the
#          world-writable /Users/Shared/OnDemandInstaller; accept only a root-owned regular file;
#          require pkgutil --check-signature to exit 0; remove the folder on every exit path
# ============================================================

echo "Office-Reset: Starting postinstall for Reset_Outlook"
autoload is-at-least
APP_NAME="Microsoft Outlook"
APP_GENERATION="2019"
DOWNLOAD_2019="https://go.microsoft.com/fwlink/?linkid=525137"
DOWNLOAD_2016="https://go.microsoft.com/fwlink/?linkid=871753"
OS_VERSION=$(sw_vers -productVersion)
SECURITY_ITEM_NOT_FOUND=44 # `security delete-*` returns exit status 44 ("item not found" / errSecItemNotFound); safe to treat as success on supported macOS versions (see `man security`).
KEYCHAIN_DELETE_FAILURE=0
STRICT_KEYCHAIN_DELETE_FAILURES=${STRICT_KEYCHAIN_DELETE_FAILURES:-0}

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

GetPrefValue() { # $1: domain, $2: key
     osascript -l JavaScript << EndOfScript
     ObjC.import('Foundation');
     ObjC.unwrap($.NSUserDefaults.alloc.initWithSuiteName('$1').objectForKey('$2'))
EndOfScript
}

GetCustomManifestVersion() {
	# Reset globals to prevent stale values from a previous call
	CUSTOM_VERSION=""
	FULL_UPDATER=""

	CHANNEL_NAME=$(GetPrefValue "com.microsoft.autoupdate2" "ChannelName")
	if [[ "${CHANNEL_NAME}" == "Custom" ]]; then
		MANIFEST_SERVER=$(GetPrefValue "com.microsoft.autoupdate2" "ManifestServer")
		echo "Office-Reset: Found custom ManifestServer ${MANIFEST_SERVER}"
		FULL_UPDATER=$(/usr/bin/nscurl --location "${MANIFEST_SERVER}/0409OPIM2019.xml" | grep -A1 -m1 'FullUpdaterLocation' | grep 'string' | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
		echo "Office-Reset: Found custom FullUpdaterLocation ${FULL_UPDATER}"
		if [[ "${FULL_UPDATER}" == "https://"* ]]; then
			CUSTOM_VERSION=$(/usr/bin/nscurl --location "${MANIFEST_SERVER}/0409OPIM2019-chk.xml" | grep -A1 -m1 'Update Version' | grep 'string' | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
			echo "Office-Reset: Found custom update version ${CUSTOM_VERSION}"
		fi
	fi
}

CleanupDownloadFolder() {
	if [[ -n "${DOWNLOAD_FOLDER}" && "${DOWNLOAD_FOLDER}" == /private/tmp/MOFA_OnDemandInstaller.* ]]; then
		/bin/rm -rf "${DOWNLOAD_FOLDER%/}"
	fi
}

RepairApp() {
	if [[ "${APP_GENERATION}" == "2016" ]]; then
		DOWNLOAD_URL="${DOWNLOAD_2016}"
	else
		DOWNLOAD_URL="${DOWNLOAD_2019}"
	fi

	# Root-private, per-run download folder. The previous fixed path under /Users/Shared was
	# writable by every local account and could be replaced with a symlink (GHSA-gw3c-6fvh-7gqm).
	DOWNLOAD_FOLDER=$(/usr/bin/mktemp -d /private/tmp/MOFA_OnDemandInstaller.XXXXXX)
	if [[ -z "${DOWNLOAD_FOLDER}" || ! -d "${DOWNLOAD_FOLDER}" ]]; then
		echo "Office-Reset: Could not create a private download folder"
		exit 1
	fi
	/bin/chmod 700 "${DOWNLOAD_FOLDER}"
	DOWNLOAD_FOLDER="${DOWNLOAD_FOLDER}/"

	GetCustomManifestVersion
	if [[ -z "${CUSTOM_VERSION}" ]]; then
		CDN_PKG_URL=$(/usr/bin/nscurl --location --head "${DOWNLOAD_URL}" --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	else
		CDN_PKG_URL="${FULL_UPDATER}"
	fi

	echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
	CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

	CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head "${CDN_PKG_URL}" --dump-header - | awk '/Content-Length/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	CDN_PKG_MB=$(( CDN_PKG_SIZE / 1000 / 1000 ))
	echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

	echo "Office-Reset: Starting ${APP_NAME} package download"
	/usr/bin/nscurl --background --download --large-download --location \
		--download-directory "${DOWNLOAD_FOLDER}" "${CDN_PKG_URL}"
	echo "Office-Reset: Finished package download"

	LOCAL_PKG="${DOWNLOAD_FOLDER}${CDN_PKG_NAME}"
	# Accept only a regular file (never a symlink) owned by the user running this script
	if [[ ! -f "${LOCAL_PKG}" || -L "${LOCAL_PKG}" || "$(/usr/bin/stat -f '%u' "${LOCAL_PKG}" 2>/dev/null)" != "$(id -u)" ]]; then
		echo "Office-Reset: Downloaded package is missing or is not a regular file owned by $(id -un)"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		CleanupDownloadFolder
		exit 1
	fi
	LOCAL_PKG_SIZE=$(stat -qf%z "${LOCAL_PKG}")
	if [[ "${LOCAL_PKG_SIZE}" == "${CDN_PKG_SIZE}" ]]; then
		echo "Office-Reset: Downloaded package is wholesome"
	else
		echo "Office-Reset: Downloaded package is malformed. Local file size: ${LOCAL_PKG_SIZE}"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		CleanupDownloadFolder
		exit 1
	fi

	PKG_SIG_OUTPUT=$(/usr/sbin/pkgutil --check-signature "${LOCAL_PKG}" 2>&1)
	PKG_SIG_STATUS=$?
	LOCAL_PKG_SIGNING=$(echo "${PKG_SIG_OUTPUT}" | awk '/Developer ID Installer/' | cut -d ':' -f2 | awk '{$1=$1};1')
	if [[ ${PKG_SIG_STATUS} -eq 0 && "${LOCAL_PKG_SIGNING}" == "Microsoft Corporation (UBF8T346G9)" ]]; then
		echo "Office-Reset: Downloaded package is signed by Microsoft"
	else
		echo "Office-Reset: Downloaded package is not signed by Microsoft"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		CleanupDownloadFolder
		exit 1
	fi

	echo "Office-Reset: Starting package install"
	/usr/sbin/installer -pkg "${LOCAL_PKG}" -target /
	if [[ $? -eq 0 ]]; then
		echo "Office-Reset: Package installed successfully"
		CleanupDownloadFolder
	else
		echo "Office-Reset: Package installation failed"
		echo "Office-Reset: Please manually download and install ${APP_NAME} from ${CDN_PKG_URL}"
		CleanupDownloadFolder
		exit 1
	fi
	echo "Office-Reset: Exiting without removing configuration data"
	exit 0
}

# Generic keychain entry finder; returns exit code of `security find-generic-password` directly.
# $1: flag (-G for generic attribute, -l for label), $2: value
FindKeychainEntry() {
	/usr/bin/security find-generic-password "$1" "$2" 2>/dev/null 1>/dev/null
}

HandleSecurityDeleteResult() {
	local status="$1"
	local item_kind="$2"
	local item_name="$3"
	local output="$4"

	if [[ "$status" -eq 0 || "$status" -eq "$SECURITY_ITEM_NOT_FOUND" ]]; then
		return 0
	fi

	echo "Office-Reset: Failed to delete ${item_kind} '${item_name}' from the keychain: ${output}" >&2
	return "$status"
}

RunDeleteCommand() {
	"$@"
	local status=$?
	if [[ $status -ne 0 && $KEYCHAIN_DELETE_FAILURE -eq 0 ]]; then
		KEYCHAIN_DELETE_FAILURE=$status
	fi
	return $status
}

DeleteInternetPasswordIfPresent() {
	local output
	local status
	output=$(/usr/bin/security delete-internet-password -s "$1" 2>&1)
	status=$?
	HandleSecurityDeleteResult "$status" "internet password" "$1" "$output"
}

DeleteGenericPasswordIfPresent() {
	local output
	local status
	output=$(/usr/bin/security delete-generic-password -l "$1" 2>&1)
	status=$?
	HandleSecurityDeleteResult "$status" "generic password label" "$1" "$output"
}

DeleteGenericPasswordByGenericAttributeIfPresent() {
	local output
	local status
	output=$(/usr/bin/security delete-generic-password -G "$1" 2>&1)
	status=$?
	HandleSecurityDeleteResult "$status" "generic password attribute" "$1" "$output"
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

# Attempt graceful quit first, then force-kill if still running
/usr/bin/pkill "Microsoft Outlook" 2>/dev/null && sleep 2
/usr/bin/pkill -9 "Microsoft Outlook" 2>/dev/null || true

if [[ -d "/Applications/Microsoft Outlook.app" ]]; then
	APP_VERSION=$(defaults read "/Applications/Microsoft Outlook.app/Contents/Info.plist" CFBundleVersion)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 16.17 "${APP_VERSION}"; then
		APP_GENERATION="2016"
	fi
	if [[ "${APP_GENERATION}" == "2019" ]]; then
		if ! is-at-least 16.73 "${APP_VERSION}" && is-at-least 11.0.0 "${OS_VERSION}"; then
			echo "Office-Reset: The installed version of ${APP_NAME} (2019 generation) is ancient. Updating it now"
			RepairApp
		fi
		GetCustomManifestVersion
		if [[ -n "${CUSTOM_VERSION}" ]] && [[ "${APP_VERSION}" != "${CUSTOM_VERSION}" ]]; then
			echo "Office-Reset: ${APP_NAME} is ${APP_VERSION} on-disk, but the pinned version has been set to ${CUSTOM_VERSION}. Removing and reinstalling"
			/bin/rm -rf "/Applications/Microsoft Outlook.app"
			RepairApp
		fi
	fi
	if [[ "${APP_GENERATION}" == "2016" ]]; then
		if ! is-at-least 16.16 "${APP_VERSION}"; then
			echo "Office-Reset: The installed version of ${APP_NAME} (2016 generation) is ancient. Updating it now"
			RepairApp
		fi
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	CODESIGN_RESULT=$(/usr/bin/codesign -vv --deep "/Applications/Microsoft Outlook.app" 2>&1)
	if [[ $? -gt 0 ]]; then
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and reporting error: ${CODESIGN_RESULT}"
		if [[ "${CODESIGN_RESULT}" == *"OLE.framework"* ]]; then
			echo "Office-Reset: Only OLE.framework has been modified. Ignoring the repair"
		else
			echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled"
			/bin/rm -rf "/Applications/Microsoft Outlook.app"
			RepairApp
		fi
	else
		echo "Office-Reset: Codesign passed successfully"
	fi
else
	echo "Office-Reset: ${APP_NAME} was not found in the default location"
fi

echo "Office-Reset: Removing configuration data for ${APP_NAME}"
/bin/rm -f /Library/Preferences/com.microsoft.Outlook.plist
/bin/rm -f "/Library/Managed Preferences/com.microsoft.Outlook.plist"
/bin/rm -f "${HOME}/Library/Preferences/com.microsoft.Outlook.plist"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Outlook"
/bin/rm -rf "${HOME}/Library/Containers/com.microsoft.Outlook.CalendarWidget"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.Outlook"
/bin/rm -rf "${HOME}/Library/Application Scripts/com.microsoft.Outlook.CalendarWidget"

/bin/rm -rf "/Library/Application Support/Microsoft/WebExPlugin"
/bin/rm -rf "/Library/Application Support/Microsoft/ZoomOutlookPlugin"
/bin/rm -rf "/Users/Shared/ZoomOutlookPlugin"

/bin/rm -rf "/Library/Application Support/Microsoft/Office365/User Content.localized/Startup.localized/Word/NormalEmail.dotm"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/User Content.localized/Startup.localized/Word/NormalEmail.dotm"

/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/DRM_Evo.plist"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/mip_policy"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/FontCache"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/ComRPC32"
/bin/rm -rf "${HOME}/Library/Group Containers/UBF8T346G9.Office/TemporaryItems"
OfficeAclFiles=("${HOME}/Library/Group Containers/UBF8T346G9.Office/Microsoft Office ACL"*(N))
if (( ${#OfficeAclFiles[@]} )); then
	/bin/rm -f "${OfficeAclFiles[@]}"
fi
/bin/rm -f "${HOME}/Library/Group Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg"

/bin/rm -rf "${TMPDIR:-/tmp}/com.microsoft.Outlook"

/bin/rm -rf "/Applications/.Microsoft Outlook.app.installBackup"

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [[ -z "$KeychainHasLogin" ]]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "${HOME}/Library/Keychains/login.keychain-db"
fi

echo "Office-Reset: Listing keychains for logged-in user"
/usr/bin/security list-keychains

while FindKeychainEntry -G 'MSOpenTech.ADAL.1'; do
	RunDeleteCommand DeleteGenericPasswordByGenericAttributeIfPresent 'MSOpenTech.ADAL.1' || break
done
RunDeleteCommand DeleteInternetPasswordIfPresent 'msoCredentialSchemeADAL'
RunDeleteCommand DeleteInternetPasswordIfPresent 'msoCredentialSchemeLiveId'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Identities Cache 2'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Identities Cache 3'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Identities Settings 2'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Identities Settings 3'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Ticket Cache'
RunDeleteCommand DeleteGenericPasswordIfPresent 'Microsoft Office Ticket Cache 2'
RunDeleteCommand DeleteGenericPasswordIfPresent 'com.microsoft.adalcache'
RunDeleteCommand DeleteGenericPasswordIfPresent 'com.microsoft.OutlookCore.Secret'
while FindKeychainEntry -l 'com.helpshift.data_com.microsoft.Outlook'; do
	RunDeleteCommand DeleteGenericPasswordIfPresent 'com.helpshift.data_com.microsoft.Outlook' || break
done
while FindKeychainEntry -l 'MicrosoftOfficeRMSCredential'; do
	RunDeleteCommand DeleteGenericPasswordIfPresent 'MicrosoftOfficeRMSCredential' || break
done
while FindKeychainEntry -l 'MSProtection.framework.service'; do
	RunDeleteCommand DeleteGenericPasswordIfPresent 'MSProtection.framework.service' || break
done
while FindKeychainEntry -l 'Exchange'; do
	RunDeleteCommand DeleteGenericPasswordIfPresent 'Exchange' || break
done

if [[ $KEYCHAIN_DELETE_FAILURE -ne 0 ]]; then
	echo "Office-Reset: Completed with one or more keychain deletion errors" >&2
	if [[ "$STRICT_KEYCHAIN_DELETE_FAILURES" == "1" ]]; then
		exit $KEYCHAIN_DELETE_FAILURE
	fi
fi

exit 0
