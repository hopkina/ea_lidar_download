#----------------------------------------------------------------
# Script name:  EA_LiDAR_ByPolygon
#
# Description:  To download EA LiDAR using a polygon to specify 
#               the area of interest
#               1. Intersects area of interest with OS grid
#                  tiles to identify those to download
#                  This script uses an index to facilitate this
#               2. Queries the EA website to return a JSON
#                  listing of products to each tile
#               3. Downloads the appropriate data 
#
# Note:         Requirement for fiona and shapely
#
# To do:        unzip?
# 
# Date created: 20180421
# Last updated: N/A
#----------------------------------------------------------------

import fiona
from shapely.geometry import shape
from rtree import index
import requests
import urllib

# setup 
aoishpfile = "C:\\gisdata\\test\\wl_ward.shp" # aoi shapefile
tileshpfile = "C:\\gisdata\\OSGB_Grids\\Shapefile\\OSGB_Grid_5km.shp" # tile shapefile
outFolder = "c:\\stuff\\" # path to folder for downloads
prodName = "LIDAR-DTM-1M-ENGLAND-EA" # specify product

# get the area of interest polygon
aoipolys = fiona.open(aoishpfile)

# get the tile polygons
tilepolys = fiona.open(tileshpfile)

# list for intersecting tile names
tileList = []

# build tile index
idx = index.Index()
for tile in tilepolys:
    fid = int(tile['id'])
    tgeom = shape(tile['geometry'])
    idx.insert(fid, tgeom.bounds)

# loop through the area of interest polys
for aoi in aoipolys:
    aoigeom = shape(aoi['geometry'])
    # intersect using index first
    for fid in list(idx.intersection(aoigeom.bounds)):
        tpoly = tilepolys[fid]
        tgeom = shape(tpoly['geometry'])
        # then using actual geometry
        if tgeom.intersects(aoigeom):
            # get the intersecting tile names
            tid = tpoly['properties']['TILE_NAME']

            # build list of intersecting tiles
            tileList.append(tid)
        
for tile in tileList:
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

                # grab it
                try:
                    urllib.request.urlretrieve(downloadurl, outpath)
                # handle errors
                except urllib.error.HTTPError as err:
                    print("HTTP Error:", err, fileName)
                except urllib.error.URLError as err:
                    print("URL Error:", err, fileName)