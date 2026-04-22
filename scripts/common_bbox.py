# ASCII-only helper for the LES/East Village/Chinatown study area
from shapely.geometry import Polygon
BOUNDARY_POLYGON_WGS84 = Polygon([(-73.9889, 40.7327),(-73.9725, 40.7327),(-73.9728, 40.7174),(-73.9950, 40.7174),(-73.9889, 40.7327)])
BOUNDARY_BBOX_WGS84 = BOUNDARY_POLYGON_WGS84.envelope.bounds
def study_area_polygon(): return BOUNDARY_POLYGON_WGS84
def study_area_bbox(): return BOUNDARY_BBOX_WGS84
