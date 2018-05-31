#-----------------------------------------------------------------------------
# Script name:  EA_LiDAR_Utilities
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
# Date created: 20180531
#-----------------------------------------------------------------------------

import fiona
from shapely.geometry import shape
from rtree import index
import requests
import urllib
import multiprocessing as mp
import os


#-------------------------------------------
# multiprocessing worker to download tiles
#-------------------------------------------
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


#--------------------------
# multiprocessing handler
#--------------------------
def mp_handler(dlInfoList):
    # setup the pool and pass to worker processes
    p = mp.Pool()
    p.starmap(mp_worker, dlInfoList)


#-----------------------------------------------
# get a list of tile ids that intersect to aoi
#-----------------------------------------------
def getTileIds(tileshapefile, aoishapefile):
    # list for intersecting tile names
    tileList = []
    # get the tile polygons
    with fiona.open(tileshapefile) as tilepolys:
        # build tile index
        idx = index.Index()
        for tile in tilepolys:
            fid = int(tile['id'])
            tgeom = shape(tile['geometry'])
            idx.insert(fid, tgeom.bounds)
    
        # get the area of interest polygon
        with fiona.open(aoishapefile) as aoipolys:
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

    # return a list of tile ids                    
    return tileList


#--------------------------------------------------------------------------
# use the tile list to query the products and get information to use to 
# build the url to download the data
#--------------------------------------------------------------------------
def getTileUrls(listOfTiles, productName, outFolder):

    dlInfoList = []

    # loop through intersecting tiles        
    for tile in listOfTiles:
        # get the first four characters for use in the url in the JSON file
        tileRef = tile[:4]
        # change the last two characters to lower case to match JSON format
        # for the full file name
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

    return dlInfoList


def main(method, 
         product,  
         outputfolder, 
         tileshapefile=None,
         aoishapefile=None,
         tileid=None):

    #-----------------------
    # VALIDATION OF INPUTS
    #-----------------------
    if method == "TILE":

        tilelist = []

        # make sure that a tileid has been supplied
        if tileid == None:
            print("Tile method specified but no tile id specified")
        else:
            # check length of tile string
            if len(tileid) == 4:
                # build a list of tileids with ne, se, sw and nw added
                # to cover the full set for a tile
                compasslist = ["ne", "se", "sw", "nw"]
                for point in compasslist:
                    # do stuff
                    fulltileid = tileid + point
                    tilelist.append(fulltileid)

            elif len(tileid) == 6:
                # convert to list
                tilelist.append(tileid)
    
    if method == "POLYGON":
        # make sure that an aoi shapefile has been supplied
        if aoishapefile == None:
            print("Polygon method specified but no aoi shapefile specified")
        # check the tile shapefile
        if tileshapefile == None:
            print("Polygon method specified but no tile shapefile specified")
        else:
            if not os.path.exists(tileshapefile):
                print("Tile shapefile is invalid")


    # check valid product name
    # don't have a complete list for this so can't yet implement
    # if product in ()

    # check for output folder (doesn't exist, create it)
    if not os.path.isdir(outputfolder):
        # os.makedirs(outputfolder)
        print("Output folder doesn't exist")

    # -----------
    # EXECUTION
    # -----------

    if method == "POLYGON":
        tilelist = getTileIds(tileshapefile, aoishapefile)

    dlInfoList = getTileUrls(tilelist, product, outputfolder)

    # use multiprocessing so that more than one item can be downloaded at once
    mp_handler(dlInfoList)

    print ("Process complete.")
        


if __name__ == '__main__':

    #--------
    # SETUP
    #--------
    METHOD = "TILE" # by TILE id or POLYGON area of interest
    TILEID = "TQ28"
    PRODUCTTODOWNLOAD = "LIDAR-DTM-1M-ENGLAND-EA" # specify product
    # tile shapefile
    TILESHPFILE = "C:\\gisdata\\OSGB_Grids\\Shapefile\\OSGB_Grid_5km.shp" 
    OUTPUTFOLDER = "c:\\stuff\\" # path to folder for downloads
    AOISHPFILE = "C:\\gisdata\\test\\wl_ward.shp" # aoi shapefile


    #----------
    # AND RUN
    #----------
    main(METHOD, PRODUCTTODOWNLOAD, OUTPUTFOLDER, TILEID)