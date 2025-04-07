echo "++++++++++++++++++++++++++++++++++++++++++++++"

DeferredRingVersion=$(curl -fsIL "https://go.microsoft.com/fwlink/?linkid=861009" | grep -i location: | cut -d "/" -f 6 | cut -d "." -f 1-3)
echo "Deferred Ring Version: $DeferredRingVersion"
DeferredRingSHA1=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861009" | sha1sum | awk '{print $1}')
DeferredRingSHA256=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861009" | sha256sum | awk '{print $1}')
echo "Deferred Ring SHA1: $DeferredRingSHA1"
echo "Deferred Ring SHA256: $DeferredRingSHA256"

UpcomingDeferredRingVersion=$(curl -fsIL "https://go.microsoft.com/fwlink/?linkid=861010" | grep -i location: | cut -d "/" -f 6 | cut -d "." -f 1-3)
echo "Upcoming Deferred Ring Version: $UpcomingDeferredRingVersion"
UpcomingDeferredRingSHA1=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861010" | sha1sum | awk '{print $1}')
UpcomingDeferredRingSHA256=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861010" | sha256sum | awk '{print $1}')
echo "Upcoming Deferred Ring SHA1: $UpcomingDeferredRingSHA1"
echo "Upcoming Deferred Ring SHA256: $UpcomingDeferredRingSHA256"

InsiderRingVersion=$(curl -sL "https://g.live.com/0USSDMC_W5T/MacODSUInsiders" | xmllint --xpath "string(//key[.='CFBundleShortVersionString']/following-sibling::string[1])" - 2>/dev/null)
InsiderRingVersionSHA256=$(curl -sL "https://g.live.com/0USSDMC_W5T/MacODSUInsiders" | xmllint --xpath "string(//key[.='UniversalPkgSha256Hash']/following-sibling::string[1])" - 2>/dev/null)

echo "Insider Ring Version: $InsiderRingVersion"
echo "Insider Ring SHA256: $InsiderRingVersionSHA256"


UpcomingProductionRingVersion=$(curl -sL "https://g.live.com/0USSDMC_W5T/StandaloneProductManifest" | \
  xmllint --xpath "string(//array/dict[1]/key[.='CFBundleShortVersionString']/following-sibling::string[1])" - 2>/dev/null)
echo "Upcoming Production Ring Version: $UpcomingProductionRingVersion"

ProductionRingVersion=$(curl -sL "https://g.live.com/0USSDMC_W5T/StandaloneProductManifest" | \
  xmllint --xpath "string(//array/dict[2]/key[.='CFBundleShortVersionString']/following-sibling::string[1])" - 2>/dev/null)
echo "Production Ring Version: $ProductionRingVersion"

echo "++++++++++++++++++++++++++++++++++++++++++++++"

RollingoutappNewVersion=$(curl -fsIL "https://go.microsoft.com/fwlink/?linkid=861011" | grep -i location: | cut -d "/" -f 6 | cut -d "." -f 1-3)
echo "Rollingout Version: $RollingoutappNewVersion"
RollingoutSHA1=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861011" | sha1sum | awk '{print $1}')
RollingoutSHA256=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=861011" | sha256sum | awk '{print $1}')
echo "Rollingout SHA1: $RollingoutSHA1"
echo "Rollingout SHA256: $RollingoutSHA256"

appNewVersion=$(curl -fsIL "https://go.microsoft.com/fwlink/?linkid=823060" | grep -i location: | cut -d "/" -f 6 | cut -d "." -f 1-3)
echo "appNewVersion: $appNewVersion"
appNewSHA1=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=823060" | sha1sum | awk '{print $1}')
appNewSHA256=$(curl -fsL "https://go.microsoft.com/fwlink/?linkid=823060" | sha256sum | awk '{print $1}')
echo "appNewVersion SHA1: $appNewSHA1"
echo "appNewVersion SHA256: $appNewSHA256"

echo "++++++++++++++++++++++++++++++++++++++++++++++"