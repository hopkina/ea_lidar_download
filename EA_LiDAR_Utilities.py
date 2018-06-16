#-----------------------------------------------------------------------------
# Script name:  EA_LiDAR_Utilities
#
# Description:  To download EA LiDAR using either a tile id or a polygon to 
#               specify the area of interest.
#               To list the available products for a tile.
#
#               Shapefile of 5k OS tiles can be sourced from:
#               https://github.com/charlesroper/OSGB_Grids
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
import argparse


def mp_worker(downloadurl, outpath):
    """ 
    Multiprocessing worker to download data 
    """

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


def mp_handler(dlinfolist):
    """ 
    Multiprocessing handler 
    """

    # setup the pool and pass to worker processes
    p = mp.Pool()
    p.starmap(mp_worker, dlinfolist)


def gettileids(aoishapefile, tileshapefile):
    """ 
    Get a list of tile ids that intersect the area of interest.
    """

    # list for intersecting tile names
    tilelist = []
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
                        tilelist.append(tid)

    # return a list of tile ids                    
    return tilelist


def gettileurls(listoftiles, productname, outfolder):
    """ 
    Use the tilelist to query the website in order to build the url(s) to
    download the data
    """

    dlinfolist = []

    # the request requires a 10k tile id
    # get a list of 10k tile ids from the full list to reduce the number of
    # requests to the website
    tilestorequest = set([tile[:4] for tile in listoftiles])

    # loop through intersecting tiles        
    for tileref in tilestorequest:

        # URL for JSON file
        jsonUrl = f"http://www.geostore.com/environment-agency/rest/product/OS_GB_10KM/{tileref}?catalogName=Survey"
        # base url for download
        baseUrl = "http://www.geostore.com/environment-agency/rest/product/download/"

        # get the json catalog listing
        ssirectoryjson = requests.get(jsonUrl)
        j = ssirectoryjson.json()

        # loop through json response
        for r in j:

            pyramid = r['pyramid']

            if pyramid == productname:
                fileguid = r['guid']
                filename = r['fileName']

                for fulltilename in listoftiles:
                    # ensure the last two characters are lower case to match 
                    # the JSON format for the full file name
                    tileend = fulltilename[4:].lower()
                    formattedtilename = fulltilename[:4] + tileend

                    # see if the tile name is in the file name
                    if formattedtilename in filename:
                        # build the full download url
                        downloadurl = baseUrl + fileguid
                        #print (downloadurl)
                        # build the output path for the zip file
                        outpath = outfolder + filename

                        # build list of tuples to pass into download using 
                        # multiprocessing
                        dlinfo = (downloadurl, outpath)
                        dlinfolist.append(dlinfo)

    return dlinfolist


def getlidarbytile (tileid, product, outputfolder):
    """ 
    Download LiDAR data using a tile id. 

    Accepts a 10k tile id or a 5k tile id.
    """

    # check for output folder
    if not os.path.isdir(outputfolder):
        # os.makedirs(outputfolder)
        return ("Output folder doesn't exist")

    tilelist = []

    # check length of tile string
    # length of four indicates 10k tile id eg TL42
    if len(tileid) == 4:
        # if a 10k tile id has been supplied build a list of tileids 
        # with ne, se, sw and nw added to cover the full set for a tile
        compasslist = ["ne", "se", "sw", "nw"]
        for point in compasslist:
            # do stuff
            fulltileid = tileid + point
            tilelist.append(fulltileid)

    # length of six indicates a 5k tile id eg TL42se
    elif len(tileid) == 6:
        # convert to list
        tilelist.append(tileid)

    # get the dataset urls
    dlinfolist = gettileurls(tilelist, product, outputfolder)

    # download the data
    # use multiprocessing so that more than one item can be downloaded 
    # at once
    mp_handler(dlinfolist)    

    return ("Process complete.")
    # bosh, we're sorted


def getlidarbyaoi(aoishapefile, tileshapefile, product, outputfolder):
    """ 
    Download LiDAR data using a polygon area of interest
    
    Requires a polygon shapefile of the area of interest.

    Requires a shapefile of 5k OS tiles.
    """
    
    # check for output folder
    if not os.path.isdir(outputfolder):
        # os.makedirs(outputfolder)
        return ("Output folder doesn't exist")

    # use polygon to find tile ids
    tilelist = gettileids(tileshapefile, aoishapefile)

    # get the dataset urls
    dlinfolist = gettileurls(tilelist, product, outputfolder)

    # download the data
    # use multiprocessing so that more than one item can be downloaded 
    # at once
    mp_handler(dlinfolist)

    return ("Process complete.")
    # bosh, we're sorted


def getproducts(tileid):
    """ 
    Get a list of the products available for a tile.
    Accepts a 10k tile id or a 5k tile id.
    """

    # use a set so that duplicates are not included in the returned list
    productset = set()

    # in case a 5k tile id has been supplied 
    # get the first four characters for use in the url
    tileid = tileid[:4]

    # URL for JSON file
    jsonurl = f"http://www.geostore.com/environment-agency/rest/product/OS_GB_10KM/{tileid}?catalogName=Survey"

    # get the json catalog listing
    sdirectoryjson = requests.get(jsonurl)
    j = sdirectoryjson.json()

    # loop through json response
    for r in j:
        productset.add(r['pyramid'])

    productlist = list(productset)
    productlist.sort()

    return productlist
        

if __name__ == '__main__':

    tileid = "TQ28"

    #-------------------
    # GET PRODUCT LIST
    #-------------------
    #result = getproducts(tileid)

    producttodownload = "LIDAR-DTM-1M-ENGLAND-EA" # specify product
    outputfolder = "C:\\stuff\\" # path to folder for downloads

    #----------------------------------
    # USE A TILE ID TO GET LIDAR DATA
    #----------------------------------
    # result = getlidarbytile(tileid, producttodownload, outputfolder)

    # tile shapefile
    tileshpfile = "C:\\gisdata\\OSGB_Grids\\Shapefile\\OSGB_Grid_5km.shp" 
    aoishpfile = "C:\\gisdata\\test\\wl_ward.shp" # aoi shapefile

    #--------------------------------------------
    # USE AN AREA OF INTEREST TO GET LIDAR DATA
    #--------------------------------------------
    result = getlidarbyaoi(aoishpfile, 
                           tileshpfile, 
                           producttodownload, 
                           outputfolder)

    print (result)