# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 22:26:52 2020

@author: MEvans
"""
import geopandas as gpd
import requests

## get list of all species with CH in CA, OR, WA
#species = list(fxn.get_species_list())
#chGpd = gpd.GeoDataFrame()
## get the CH geojson for each species 1 by 1 to avoid timeout
#for i in range(len(species)):
#    spJson = fxn.get_ch_json([species[i]])
#    spGpd = gpd.GeoDataFrame.from_features(spJson['features'])
#    chGpd = chGpd.append(spGpd)
# 
#
#
#chSubset = gpd.sjoin(ch, studyArea, 'inner', 'within')[['comname', 'geometry', 'sciname']]

# Get state data
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
statesGpd = gpd.read_file('data/cb_2019_us_state_20m.kml', driver = 'KML')

# Create a subset of west coast states and define projection
studyArea = statesGpd[statesGpd.Name.str.contains('California|Oregon|Washington')]
sa = studyArea.geometry.unary_union
#sa_json = gpd.GeoSeries([sa]).to_json()
#sa_dict = json.loads(sa_json)
bbox = sa.bounds

def make_range_data():
    ranges = gpd.read_file('data/usfws_complete_species_current_range.shp', bbox = bbox)
    ranges = ranges[['SPCODE', 'SCINAME', 'COMNAME', 'STATUS_ABB', 'geometry']]
    te = ranges[ranges.STATUS_ABB.str.match('Endangered|Threatened')]
    te.geometry = te.buffer(0)
    non_duplicated = te.drop_duplicates(['SPCODE'], keep = False)
    duplicates = te[te.duplicated(['SPCODE'], keep = False)]
    dissolved = duplicates.dissolve(by = 'SPCODE').reset_index()
    merged = dissolved.append(non_duplicated)
    merged['Area'] = merged.geometry.to_crs(3395).area
    # leave the range data in its native 4326 - seems to work faster in subsequent bbox searches
    merged.to_file('data/rangeGPD.shp')

# define a list of table columns we are interested in 
columns = ['OBJECTID_1', 'comname', 'sciname', 'spcode', 'status', 'effectdate', 'GlobalID', 'Shape__Area']
# Final CH POlygons are featuer layer 1
final_polygons = '1'

def get_ch_data():
    """Retrieve USFWS CH Polygons (final)
    https://fws.maps.arcgis.com/home/webmap/viewer.html?webmap=9d8de5e265ad4fe09893cf75b8dbfb77
    """
    url = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/USFWS_Critical_Habitat/FeatureServer/{}/query'
    #TODO convert dict style to string for readability
#    payload = {
#            'where':'1%3D1',
#            'geometry': f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}',
#            'geometryType':'esriGeometryEnvelope',
#            'spatialRel':'esriSpatialRelIntersects',
#            'outFields':f'{colList[1]},{colList[2]},{colList[3]},{colList[4]}',
#            'f':'geoJSON'}
#    params = urllib.parse.urlencode(payload, safe=':+')
    # for now, we can pass a literal string to the params argument of requests.get
    params = f"where=sciname+LIKE+%27%25%27&objectIds=&time=&outFields={columns[0]},{columns[1]},{columns[2]},{columns[3]},{columns[4]},{columns[5]},{columns[6]},{columns[7]}&f=geoJSON&geometryType=esriGeometryEnvelope&geometry={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&spatialRel=esriSpatialRelIntersects&inSR=4326"
    request = requests.get(url.format(final_polygons), params = params)
    chJson = request.json()
    
    gdf = gpd.GeoDataFrame.from_features(chJson['features']).set_crs(epsg=4326)
    # we need to buffer by zero to fix any invalid geometries
    gdf.geometry = gdf.buffer(0)

    print('size of filtered data', len(gdf))
    
    dissolved = gdf[gdf.geometry.is_valid].dissolve(by = 'sciname')
#    subset = gpd.sjoin(dissolved, studyArea, 'inner', 'within')
    dissolved['Area'] = dissolved.geometry.to_crs(epsg=3395).area
    dissolved.to_file('data/chGPD.geojson', driver = 'GeoJSON')
