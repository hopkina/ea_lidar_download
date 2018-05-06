#----------------------------------------------------------------
# Script name:  EA_LiDAR_ByPolygon_SJoin
#
# Description:  To download EA LiDAR using a polygon to specify 
#               the area of interest
#               1. Intersects area of interest with OS grid
#                  tiles to identify those to download
#                  This script uses a spatial join to do this
#               2. Queries the EA website to return a JSON
#                  listing of products to each tile
#               3. Downloads the appropriate data 
#
# Note:         Requirement for geopandas
#
# To do:        unzip?
# 
# Date created: 20180421
# Last updated: N/A
#----------------------------------------------------------------

import geopandas
from geopandas.tools import sjoin
import requests
import urllib

# setup 
aoishpfile = "C:\\gisdata\\test\\wl_ward.shp" # aoi shapefile
tileshpfile = "C:\\gisdata\\OSGB_Grids\\Shapefile\\OSGB_Grid_5km.shp" # tile shapefile
outFolder = "C:\\stuff\\" # path to folder for downloads
prodName = "LIDAR-DTM-1M-ENGLAND-EA" # specify product

# get the area of interest polygon
aoipolys = geopandas.GeoDataFrame.from_file(aoishpfile)

# get the tile polygons
tilepolys = geopandas.GeoDataFrame.from_file(tileshpfile)

# spatial join of the two datasets
tilesInAoi = sjoin(tilepolys, aoipolys, how='inner', op='intersects')
   
for tile in tilesInAoi.TILE_NAME:

    # get the first four characters for use in the url in the JSON file
    tileRef = tile[:4]
    # change the last two characters to lower case to match JSON format for the full file name
    tileEnd = tile[4:].lower()
    formattedTileName = tileRef + tileEnd

    # URL for JSON file (found by examining files downloaded by page load)
    jsonUrl = "http://www.geostore.com/environment-agency/rest/product/OS_GB_10KM/" + tileRef + "?catalogName=Survey"
    # base url for download
    baseUrl = "http://www.geostore.com/environment-agency/rest/product/download/"

    # get the json catalog listing
    sDirectoryJson = requests.get(jsonUrl)
    j = sDirectoryJson.json()

    # loop through json response
    for r in j:

        pyramid = r['pyramid']

        if pyramid == prodName:
            fileGuid = r['guid']
            fileName = r['fileName']

            # see if the tile name is in the file name
            if formattedTileName in fileName:
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