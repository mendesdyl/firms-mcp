"""Synthetic FIRMS area-API CSV responses built from FIRMS's documented attributes.

Column sets follow the FIRMS attribute pages (MODIS/VIIRS) and the Landsat attribute
table in the FIRMS FAQ. To be replaced with recorded live responses (MAP_KEY removed) once
running-list item LU-03 is closed.
"""

VIIRS_NOAA20_NRT = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
34.07012,-118.55011,367.0,0.39,0.36,2025-01-08,0942,N20,VIIRS,h,2.0NRT,295.1,45.2,N
34.08033,-118.54022,340.5,0.39,0.36,2025-01-08,942,N20,VIIRS,n,2.0NRT,290.0,12.7,N
34.10200,-118.20100,310.2,0.40,0.37,2025-01-08,2041,N20,VIIRS,l,2.0URT,288.0,3.1,D
"""

MODIS_NRT = """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight
34.0500,-118.5000,330.1,1.1,1.0,2025-01-08,1830,Aqua,MODIS,85,6.1NRT,300.2,60.5,D
34.0600,-118.5100,315.0,1.1,1.0,2025-01-08,1830,Aqua,MODIS,45,6.1NRT,298.0,20.0,D
34.0700,-118.5200,305.0,1.1,1.0,2025-01-08,1830,Terra,MODIS,12,6.1RT,296.0,,D
"""

MODIS_SP = """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type
19.4210,-155.2870,350.0,1.0,1.0,2018-05-20,0815,T,MODIS,100,6.1,290.0,150.3,N,1
"""

LANDSAT_NRT = """latitude,longitude,path,row,scan,track,acq_date,acq_time,satellite,confidence,daynight
34.1000,-118.6000,41,36,3542,2840,2025-01-08,18:25,L9,H,D
34.1010,-118.6010,41,36,3543,2840,2025-01-08,18:25,L9,M,D
"""

WITH_UNKNOWN_COLUMN = """latitude,longitude,acq_date,acq_time,satellite,confidence,frp,daynight,new_field
10.0,20.0,2026-10-08,0100,N21,n,1.5,N,surprise
"""

HEADER_ONLY = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,"
    "confidence,version,bright_ti5,frp,daynight\n"
)

MAP_KEY = "0123456789abcdef0123456789abcdef"  # 32 characters, test value only
OTHER_KEY = "fedcba9876543210fedcba9876543210"
