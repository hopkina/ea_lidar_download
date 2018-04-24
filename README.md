# ea_lidar_download

Python script to download EA Lidar from
https://environment.data.gov.uk/ds/survey/#/survey
using a polygon to specify the area of interest.

1. Intersects area of interest with OS grid tiles to identify 
those to download.  An index is used to facilitate this.
2. Queries the EA website to return a JSON listing of 
products for each tile
3. Downloads the appropriate data 

