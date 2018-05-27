#------------------------------------------------------------------------------
# Script name:  EA_LiDAR_ByPolygon
#
# Description:  To download EA LiDAR using a polygon to specify the area of 
#               interest.
#               1. Intersects area of interest with OS grid tiles to identify 
#                  those to download.
#                  An index is used to facilitate this.
#               2. Queries the EA website to return a JSON listing of 
#                  products for each tile
#               3. Downloads the appropriate data 
# 
# Date created: 20180421
# Last updated: 20180522 ANH
#------------------------------------------------------------------------------

import fiona
from shapely.geometry import shape
from rtree import index
import requests
import urllib
import multiprocessing as mp

def mp_worker(downloadurl, outpath):
    # worker process for download
    print (f"Downloading from: {downloadurl}")

    # grab it
    try:
        urllib.request.urlretrieve(downloadurl, outpath)
    # handle errors
    except urllib.error.HTTPError as err:
        print("HTTP Error:", err, outpath)
    except urllib.error.URLError as err:
        print("URL Error:", err, outpath)

    print (f"Download complete: {outpath}")

def mp_handler(dlInfoList):
    # setup the pool and pass to worker processes
    p = mp.Pool()
    p.starmap(mp_worker, dlInfoList)

if __name__ == '__main__':    

    # setup 
    aoishpfile = "C:\\gisdata\\test\\wl_ward.shp" # aoi shapefile
    # tile shapefile
    tileshpfile = "C:\\gisdata\\OSGB_Grids\\Shapefile\\OSGB_Grid_5km.shp" 
    outFolder = "c:\\stuff\\" # path to folder for downloads
    productName = "LIDAR-DTM-1M-ENGLAND-EA" # specify product
    #productName = "LIDAR-DSM-1M-ENGLAND-EA" # specify product

    # list for intersecting tile names
    tileList = []

    # list for download info
    dlInfoList = []

    # get the tile polygons
    with fiona.open(tileshpfile) as tilepolys:
        # build tile index
        idx = index.Index()
        for tile in tilepolys:
            fid = int(tile['id'])
            tgeom = shape(tile['geometry'])
            idx.insert(fid, tgeom.bounds)
    
        # get the area of interest polygon
        with fiona.open(aoishpfile) as aoipolys:
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
        # change the last two characters to lower case to match JSON format for
        # the full file name
        tileEnd = tile[4:].lower()
        formattedTileName = tileRef + tileEnd

        # URL for JSON file
        jsonUrl = f"http://www.geostore.com/environment-agency/rest/product/OS_GB_10KM/{tileRef}?catalogName=Survey"
        # base url for download
        baseUrl = "http://www.geostore.com/environment-agency/rest/product/download/"

        # get the json catalog listing
        sDirectoryJson = requests.get(jsonUrl)
        j = sDirectoryJson.json()

        # loop through json response
        for r in j:

            pyramid = r['pyramid']

            if pyramid == productName:
                fileGuid = r['guid']
                fileName = r['fileName']

                # see if the tile name is in the file name
                if formattedTileName in fileName:
                    # build the full download url
                    downloadurl = baseUrl + fileGuid
                    #print (downloadurl)
                    # build the output path for the zip file
                    outpath = outFolder + fileName

                    # build list of tuples to pass into download using 
                    # multiprocessing
                    dlInfo = (downloadurl, outpath)
                    dlInfoList.append(dlInfo)

    # use multiprocessing so that more than one item can be downloaded at once
    mp_handler(dlInfoList)

    print ("Process complete.")