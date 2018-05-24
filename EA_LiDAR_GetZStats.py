#-----------------------------------------------------------------------------
# Script name:  EA_LiDAR_GetZStats
#
# Description:  To get zonal stats from EA LiDAR tiles
#               1. Build vrt of tiles
#               2. Zonal Stats
#               3. Write out to new shapefile    
# 
# Date created: 20180423
# Last updated: 20180523 ANH
#-----------------------------------------------------------------------------

from osgeo import gdal
import glob
from rasterstats import zonal_stats
import fiona

inshp  = "C:\\gisdata\\test\\wl_ward.shp"
livrt  = "C:\\gisdata\\test\\LIDAR-DTM-1M-WL.vrt"
outshp = "C:\\gisdata\\test\\wl_ward_zstats.shp"

# build vrt from all ascii files
gdal.BuildVRT(livrt, glob.glob("C:\\stuff\\LIDAR-DTM-1M-*\\*.asc"))

# get the input schema to use for output
with fiona.open(inshp) as input:
    output_schema = input.schema.copy()

# add stats fields to the schema
output_schema['properties']['min'] = 'float'
output_schema['properties']['max'] = 'float'
output_schema['properties']['mean'] = 'float'
output_schema['properties']['count'] = 'float'

#--------------
# zonal stats
#--------------
stats = zonal_stats(inshp,
                    livrt,
                    geojson_out=True)

# write out to shapefile
with fiona.open(outshp, 
                'w', 
                'ESRI Shapefile', 
                output_schema, 
                crs=input.crs) as output:
    for i, feat in enumerate(stats): 
        fproperties = stats[i]['properties']
        fgeometry = stats[i]['geometry']

        output.write({'properties': fproperties,'geometry': fgeometry})