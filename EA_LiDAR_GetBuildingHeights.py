#-----------------------------------------------------------------------------
# Script name:  EA_LiDAR_GetBuildingHeights
#
# Description:  To get building heghts from EA LiDAR tiles
#               OS OpenMap buildings are used for the building outlines
#               1. Build vrt of tiles
#               2. Zonal Stats to get the mean height of the building
#               3. Write out to new shapefile    
# 
# Date created: 20180524
# Last updated: 
#-----------------------------------------------------------------------------

from osgeo import gdal
import glob
import numpy
from rasterstats import zonal_stats
import rasterio
import fiona

dtmvrt  = "C:\\gisdata\\test\\LIDAR-DTM-1M-WL.vrt"
dsmvrt  = "C:\\gisdata\\test\\LIDAR-DSM-1M-WL.vrt"
zoneshp = "C:\\gisdata\\os\\OS_OpenMap\\data\\Building_WL.shp"
heightshp = "C:\\gisdata\\test\\wl_heights.shp"

# DTM
gdal.BuildVRT(dtmvrt, glob.glob("C:\\stuff\\LIDAR-DTM-1M-*\\*.asc"))

# DSM
gdal.BuildVRT(dsmvrt, glob.glob("C:\\stuff\\LIDAR-DSM-1M-*\\*.asc"))

with rasterio.open(dtmvrt) as dtm:
    dtmarray = dtm.read(1)
    dtmaffine = dtm.affine

with rasterio.open(dsmvrt) as dsm:
    dsmarray = dsm.read(1)
    dsmaffine = dsm.affine

#------------------------------------------------------
# take the dtm heights from the dsm to get the height
#------------------------------------------------------
heightarray = dsmarray - dtmarray

#--------------
# zonal stats
#--------------
stats = zonal_stats(zoneshp,
                    heightarray,
                    affine=dtmaffine,
                    stats="mean",
                    geojson_out=True)

# get the input schema to use for output
with fiona.open(zoneshp) as input:
    output_schema = input.schema.copy()

# add stats fields to the schema
output_schema['properties']['mean'] = 'float'

# write out to shapefile
with fiona.open(heightshp, 
                'w', 
                'ESRI Shapefile', 
                output_schema, 
                crs=input.crs) as output:
    for i, feat in enumerate(stats): 
        fproperties = stats[i]['properties']
        fgeometry = stats[i]['geometry']

        output.write({'properties': fproperties,'geometry': fgeometry})