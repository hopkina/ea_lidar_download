#----------------------------------------------------------------
# Script name:  EA_LiDAR
#
# Description:  To download EA LiDAR using an OS 10k tile name
#               Easy to modify to download full dataset for
#               country  
#
# Note:         Requirement for fiona and shapely
# 
# Date:         20180421
# Last updated: N/A
#----------------------------------------------------------------

import urllib
import requests

# specify tile reference
tileRef = "TQ28"
# specify product
prodName = "LIDAR-DTM-1M-ENGLAND-EA"
# specify path to folder for downloads
outFolder = "c:\\stuff\\"

# URL for JSON file (found by examining files downloaded by page load)
jsonUrl = "http://www.geostore.com/environment-agency/rest/product/OS_GB_10KM/" + tileRef + "?catalogName=Survey"
# base url for download
baseUrl = "http://www.geostore.com/environment-agency/rest/product/download/"

# get the json catalog listing
sDirectoryJson = requests.get(jsonUrl)
j = sDirectoryJson.json()

# loop through JSON response
for r in j:

    pyramid = r['pyramid']

    if pyramid == prodName:
        fileGuid = r['guid']
        fileName = r['fileName']

        # build the full download url
        downloadurl = baseUrl + fileGuid
        print (downloadurl)
        # build the output path for the zip file
        outpath = outFolder + fileName
        print (outpath)

        # grab it
        try:
            urllib.request.urlretrieve(downloadurl, outpath)
        # handle errors
        except urllib.error.HTTPError as err:
            print("HTTP Error:", err, fileName)
        except urllib.error.URLError as err:
            print("URL Error:", err, fileName)