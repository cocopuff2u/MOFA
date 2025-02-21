#!/bin/zsh

echo "Office-Reset: Starting postinstall for Reset_Outlook"
autoload is-at-least
APP_NAME="Microsoft Outlook"
APP_GENERATION="2019"
DOWNLOAD_2019="https://go.microsoft.com/fwlink/?linkid=525137"
DOWNLOAD_2016="https://go.microsoft.com/fwlink/?linkid=871753"
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

GetPrefValue() { # $1: domain, $2: key
     osascript -l JavaScript << EndOfScript
     ObjC.import('Foundation');
     ObjC.unwrap($.NSUserDefaults.alloc.initWithSuiteName('$1').objectForKey('$2'))
EndOfScript
}

GetCustomManifestVersion() {
	CHANNEL_NAME=$(GetPrefValue "com.microsoft.autoupdate2" "ChannelName")
	if [ "${CHANNEL_NAME}" = "Custom" ]; then
    	MANIFEST_SERVER=$(GetPrefValue "com.microsoft.autoupdate2" "ManifestServer")
    	echo "Office-Reset: Found custom ManifestServer ${MANIFEST_SERVER}"
    	FULL_UPDATER=$(/usr/bin/nscurl --location ${MANIFEST_SERVER}/0409OPIM2019.xml | grep -A1 -m1 'FullUpdaterLocation' | grep 'string' | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
    	echo "Office-Reset: Found custom FullUpdaterLocation ${FULL_UPDATER}"
    	if [[ "${FULL_UPDATER}" = "https://"* ]]; then
    		CUSTOM_VERSION=$(/usr/bin/nscurl --location ${MANIFEST_SERVER}/0409OPIM2019-chk.xml | grep -A1 -m1 'Update Version' | grep 'string' | sed -e 's,.*<string>\([^<]*\)</string>.*,\1,g')
    		echo "Office-Reset: Found custom update version ${CUSTOM_VERSION}"
    	fi
    fi
}

RepairApp() {
	if [[ "${APP_GENERATION}" == "2016" ]]; then
		DOWNLOAD_URL="${DOWNLOAD_2016}"
	else
		DOWNLOAD_URL="${DOWNLOAD_2019}"
	fi

	DOWNLOAD_FOLDER="/Users/Shared/OnDemandInstaller/"
	if [ -d "$DOWNLOAD_FOLDER" ]; then
		rm -rf "$DOWNLOAD_FOLDER"
	fi
	mkdir -p "$DOWNLOAD_FOLDER"

	GetCustomManifestVersion
	if [[ -z "${CUSTOM_VERSION}" ]]; then
		CDN_PKG_URL=$(/usr/bin/nscurl --location --head $DOWNLOAD_URL --dump-header - | awk '/Location/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	else
		CDN_PKG_URL="${FULL_UPDATER}"
	fi
	
	echo "Office-Reset: Package to download is ${CDN_PKG_URL}"
	CDN_PKG_NAME=$(/usr/bin/basename "${CDN_PKG_URL}")

	CDN_PKG_SIZE=$(/usr/bin/nscurl --location --head $CDN_PKG_URL --dump-header - | awk '/Content-Length/' | cut -d ' ' -f2 | tail -1 | awk '{$1=$1};1')
	CDN_PKG_MB=$(/bin/expr ${CDN_PKG_SIZE} / 1000 / 1000)
	echo "Office-Reset: Download package is ${CDN_PKG_MB} megabytes in size"

	echo "Office-Reset: Starting ${APP_NAME} package download"
	/usr/bin/nscurl --background --download --large-download --location --download-directory $DOWNLOAD_FOLDER $CDN_PKG_URL
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
	echo "Office-Reset: Exiting without removing configuration data"
	exit 0
}

FindEntryOpenTech() {
	/usr/bin/security find-generic-password -G 'MSOpenTech.ADAL.1' 2> /dev/null 1> /dev/null
	echo $?
}
FindEntryHelpShift() {
	/usr/bin/security find-generic-password -l 'com.helpshift.data_com.microsoft.Outlook' 2> /dev/null 1> /dev/null
	echo $?
}
FindEntryRMSCredential() {
	/usr/bin/security find-generic-password -l 'MicrosoftOfficeRMSCredential' 2> /dev/null 1> /dev/null
	echo $?
}
FindEntryProtectionService() {
	/usr/bin/security find-generic-password -l 'MSProtection.framework.service' 2> /dev/null 1> /dev/null
	echo $?
}
FindEntryExchange() {
	/usr/bin/security find-generic-password -l 'Exchange' 2> /dev/null 1> /dev/null
	echo $?
}

## Main
LoggedInUser=$(GetLoggedInUser)
SetHomeFolder "$LoggedInUser"
echo "Office-Reset: Running as: $LoggedInUser; Home Folder: $HOME"

/usr/bin/pkill -9 'Microsoft Outlook'

if [ -d "/Applications/Microsoft Outlook.app" ]; then
	APP_VERSION=$(defaults read /Applications/Microsoft\ Outlook.app/Contents/Info.plist CFBundleVersion)
	echo "Office-Reset: Found version ${APP_VERSION} of ${APP_NAME}"
	if ! is-at-least 16.17 $APP_VERSION; then
		APP_GENERATION="2016"
	fi
	if [[ "${APP_GENERATION}" == "2019" ]]; then
		if ! is-at-least 16.73 $APP_VERSION && is-at-least 11.0.0 $OS_VERSION; then
			echo "Office-Reset: The installed version of ${APP_NAME} (2019 generation) is ancient. Updating it now"
			RepairApp
		fi
		GetCustomManifestVersion
		if [[ "${CUSTOM_VERSION}" ]] && [[ "${APP_VERSION}" != "${CUSTOM_VERSION}" ]]; then
			echo "Office-Reset: ${APP_NAME} is ${APP_VERSION} on-disk, but the pinned version has been set to ${CUSTOM_VERSION}. Removing and reinstalling"
			/bin/rm -rf /Applications/Microsoft\ Outlook.app
			RepairApp
		fi
	fi
	if [[ "${APP_GENERATION}" == "2016" ]]; then
		if ! is-at-least 16.16 $APP_VERSION; then
			echo "Office-Reset: The installed version of ${APP_NAME} (2016 generation) is ancient. Updating it now"
			RepairApp
		fi
	fi
	echo "Office-Reset: Checking the app bundle for corruption"
	/usr/bin/codesign -vv --deep /Applications/Microsoft\ Outlook.app
	if [ $? -gt 0 ]; then
		CODESIGN_ERROR=$(/usr/bin/codesign -vv --deep /Applications/Microsoft\ Outlook.app)
		echo "Office-Reset: The ${APP_NAME} app bundle is damaged and reporting error ${CODESIGN_ERROR}"
		if [[ "${CODESIGN_ERROR}" = *"OLE.framework"* ]]; then
			echo "Office-Reset: Only OLE.framework has been modified. Ignoring the repair"
		else
			echo "Office-Reset: The ${APP_NAME} app bundle is damaged and will be removed and reinstalled"
			/bin/rm -rf /Applications/Microsoft\ Outlook.app
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
/bin/rm -f /Library/Managed\ Preferences/com.microsoft.Outlook.plist
/bin/rm -f $HOME/Library/Preferences/com.microsoft.Outlook.plist
/bin/rm -rf $HOME/Library/Containers/com.microsoft.Outlook
/bin/rm -rf $HOME/Library/Containers/com.microsoft.Outlook.CalendarWidget
/bin/rm -rf $HOME/Library/Application\ Scripts/com.microsoft.Outlook
/bin/rm -rf $HOME/Library/Application\ Scripts/com.microsoft.Outlook.CalendarWidget

/bin/rm -rf /Library/Application\ Support/Microsoft/WebExPlugin
/bin/rm -rf /Library/Application\ Support/Microsoft/ZoomOutlookPlugin
/bin/rm -rf /Users/Shared/ZoomOutlookPlugin

/bin/rm -rf /Library/Application\ Support/Microsoft/Office365/User\ Content.localized/Startup.localized/Word/NormalEmail.dotm
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.Office/User\ Content.localized/Startup.localized/Word/NormalEmail.dotm

/bin/rm -f $HOME/Library/Group\ Containers/UBF8T346G9.Office/DRM_Evo.plist
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.Office/mip_policy
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.Office/FontCache
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.Office/ComRPC32
/bin/rm -rf $HOME/Library/Group\ Containers/UBF8T346G9.Office/TemporaryItems
/bin/rm -f $HOME/Library/Group\ Containers/UBF8T346G9.Office/Microsoft\ Office\ ACL*
/bin/rm -f $HOME/Library/Group\ Containers/UBF8T346G9.Office/MicrosoftRegistrationDB.reg

/bin/rm -rf $TMPDIR/com.microsoft.Outlook

/bin/rm -rf /Applications/.Microsoft\ Outlook.app.installBackup

KeychainHasLogin=$(/usr/bin/security list-keychains | grep 'login.keychain')
if [ "$KeychainHasLogin" = "" ]; then
	echo "Office-Reset: Adding user login keychain to list"
	/usr/bin/security list-keychains -s "$HOME/Library/Keychains/login.keychain-db"
fi

echo "Display list-keychains for logged-in user"
/usr/bin/security list-keychains

/usr/bin/security delete-internet-password -s 'msoCredentialSchemeADAL'
/usr/bin/security delete-internet-password -s 'msoCredentialSchemeLiveId'
while [[ $(FindEntryOpenTech) -eq 0 ]]; do
	/usr/bin/security delete-generic-password -G 'MSOpenTech.ADAL.1'
done
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 2'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Cache 3'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 2'
/usr/bin/security delete-generic-password -l 'Microsoft Office Identities Settings 3'
/usr/bin/security delete-generic-password -l 'Microsoft Office Ticket Cache'
/usr/bin/security delete-generic-password -l 'Microsoft Office Ticket Cache 2'
/usr/bin/security delete-generic-password -l 'com.microsoft.adalcache'
/usr/bin/security delete-generic-password -l 'com.microsoft.OutlookCore.Secret'
while [[ $(FindEntryHelpShift) -eq 0 ]]; do
	/usr/bin/security delete-generic-password -l 'com.helpshift.data_com.microsoft.Outlook'
done
while [[ $(FindEntryRMSCredential) -eq 0 ]]; do
	/usr/bin/security delete-generic-password -l 'MicrosoftOfficeRMSCredential'
done
while [[ $(FindEntryProtectionService) -eq 0 ]]; do
	/usr/bin/security delete-generic-password -l 'MSProtection.framework.service'
done

while [[ $(FindEntryExchange) -eq 0 ]]; do
	/usr/bin/security delete-generic-password -l 'Exchange'
done

exit 0