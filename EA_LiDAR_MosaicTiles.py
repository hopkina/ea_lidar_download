#------------------------------------------------------------------------------
# Script name:  EA_LiDAR_ByPolygon
#
# Description:  To mosiac EA LiDAR tiles
#
# Note:         
#
# To do:        
# 
# Date created: 20180423
# Last updated: --
#------------------------------------------------------------------------------

from osgeo import gdal
import glob

# build vrt from all ascii files
gdal.BuildVRT("c:\\stuff\\LIDAR-DTM-1M-WL.vrt", glob.glob("c:\\stuff\\LIDAR-DTM-1M-*\\*.asc"))

# clip to mask
