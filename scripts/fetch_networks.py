import json

import requests
import geopandas as gpd



url = "https://services.arcgis.com/ciPnsNFi1JLWVjva/ArcGIS/rest/services/CECONY_NetworkLCSD_Prod/FeatureServer/0/query"




# https://services.arcgis.com/ciPnsNFi1JLWVjva/ArcGIS/rest/services/CECONY_Network_Storage_Prod/FeatureServer/query?layerDefs=&geometry=&geometryType=esriGeometryPolyline&inSR=&spatialRel=esriSpatialRelIntersects&outSR=&datumTransformation=&applyVCSProjection=false&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&returnIdsOnly=false&returnCountOnly=false&returnDistinctValues=false&returnZ=false&returnM=false&sqlFormat=none&f=html&token=
polygon = {
    "rings": [[
        [-74.0138605619573, 40.699931258888974],
        [-73.97273321585372, 40.71038877726289],
        [-73.91305210667927, 40.80081360679727],
        [-73.9663628642715, 40.82014668398693],
        [-74.0203725505712, 40.74375657684307],
        [-74.0138605619573, 40.699931258888974]
    ]],
    "spatialReference": {"wkid": 4326}
}


40.69660112643715,-74.01791453959159
40.70239238830796,-73.99558495658042

params = {
    "where": "1=1",
    "outFields": "*",
    "geometry": json.dumps(polygon),
    "geometryType": "esriGeometryPolygon",
    "inSR": "4326",
    "spatialRel": "esriSpatialRelIntersects",
    "returnGeometry": "true",
    "f": "geojson"
}



r = requests.get(url, params=params)
#prefix the file path with '<DRIVER>:', e.g. 'CSV:path'.
with open("coned_network.geojson", "w") as f:
    f.write(r.text)

gdf = gpd.read_file("coned_network.geojson", driver="GeoJSON")

print(gdf.columns)
print(len(gdf))
print(r.url)
