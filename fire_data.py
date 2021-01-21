# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 11:05:52 2020

@author: MEvans
"""
import geopandas as gpd
import pandas as pd
#import folium
import requests
from datetime import datetime, date


## get current date
today = date.today()
print(today)

# Get state data
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
statesGpd = gpd.read_file('data/cb_2019_us_state_20m.kml', driver = 'KML')

# Create a subset of west coast states and define projection
studyArea = statesGpd[statesGpd.Name.str.contains('California|Oregon|Washington')]

# define fire columns were interested in
colList = ['geometry', 'ComplexName', 'DateCurrent', 'CreateDate', 'GlobalID', 'IncidentName']

## Use the Interagency Fire Data Portal to get current and past fire data
# https://data-nifc.opendata.arcgis.com/datasets/wildfire-perimeters
def recursive_fire_data(url, begin, finish, split, ls):

    dates = pd.date_range(begin, finish, split).tolist()

    for i in range(1, len(dates)):
        start = datetime.strftime(dates[i-1], '%Y-%m-%d')
        end = datetime.strftime(dates[i], '%Y-%m-%d')
        
        print(start, end)
        
        updatedURL = url.format(start, end)
        request = requests.get(updatedURL)
        json = request.json()
        
        # if we get an error, run again recursively on half the date range
        if 'error' in json.keys():
            print('error')
            recursive_fire_data(url, start, end, 3, ls)
        
        # if no error, and features in the payload create a geodataframe and append to running list
        elif len(json['features']) > 0:
            gdf = gpd.GeoDataFrame.from_features(json['features']).set_crs(epsg=4326)
            print(len(gdf))
            ls.append(gdf)
        
        # otherwise, continue to next loop iteration
        else:
            continue
            
def get_current_data():
    # create empty list to hold temporal subset geodataframes
    gpdList = []
    # define base url of api that will be modified with dates
    fireURL = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Public_Wildfire_Perimeters_View/FeatureServer/0/query?where=DateCurrent%20%3E%3D%20TIMESTAMP%20%27{}%2000%3A00%3A00%27%20AND%20DateCurrent%20%3C%3D%20TIMESTAMP%20%27{}%2000%3A00%3A00%27&outFields=*&geometry=%5B%5B%5B-125.25859375%2C%2049.05565283019709%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-124.6873046875%2C%2039.69425229061023%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-121.1716796875%2C%2034.32955443278273%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-117.5681640625%2C%2032.235755670897845%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-114.975390625%2C%2032.45851121119902%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.19609375%2C%2031.151423633862105%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-108.9548828125%2C%2031.189024707915397%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-109.1306640625%2C%2040.96720543432847%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.108203125%2C%2041.066677669125276%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.0642578125%2C%2044.57849399879169%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-112.95390625%2C%2044.484512810104995%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-116.2498046875%2C%2049.026845997157295%5D%5D%5D&geometryType=esriGeometryPolygon&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&f=geojson'
    # get today's date
    today = datetime.strftime(date.today(), '%Y-%m-%d')
    # recursively get current fire data for 2021
    recursive_fire_data(fireURL, '2020-12-15', today, 6, gpdList)
    # create single geodataframe from list of geodataframe subsets
    df = gpd.GeoDataFrame(
            pd.concat(gpdList, axis = 0, ignore_index = True),
            crs = gpdList[0].crs
            )
    # select fire polygons within CA, OR, WA study area
    subset = gpd.sjoin(df, studyArea, 'inner', 'within')[colList]
    # write fire polygons to file
    subset['Area'] = subset.geometry.to_crs(epsg=3395).area
    subset.to_file('data/fireGPD.geojson', driver = 'GeoJSON')
    
    
#firesRequest = requests.get('https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Public_Wildfire_Perimeters_View/FeatureServer/0/query?where=1%3D1&outFields=*&geometry=%5B%5B%5B-125.25859375%2C%2049.05565283019709%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-124.6873046875%2C%2039.69425229061023%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-121.1716796875%2C%2034.32955443278273%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-117.5681640625%2C%2032.235755670897845%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-114.975390625%2C%2032.45851121119902%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.19609375%2C%2031.151423633862105%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-108.9548828125%2C%2031.189024707915397%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-109.1306640625%2C%2040.96720543432847%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.108203125%2C%2041.066677669125276%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-111.0642578125%2C%2044.57849399879169%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-112.95390625%2C%2044.484512810104995%5D%2C%20%20%20%20%20%20%20%20%20%20%20%5B-116.2498046875%2C%2049.026845997157295%5D%5D%5D&geometryType=esriGeometryPolygon&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&f=geojson')

#oldFiresRequest = requests.get("https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Public_Wildfire_Perimeters_View/FeatureServer/0/query?where=DateCurrent%20%3E%3D%20TIMESTAMP%20'2020-06-01%2000%3A00%3A00'%20AND%20DateCurrent%20%3C%3D%20TIMESTAMP%20'{}%2000%3A00%3A00'&outFields=*&outSR=4326&f=geojson".format(datetime.datetime.strftime(today, '%Y-%m-%d')))

def get_2020_data():
    """Retrieve 2020 burned area data from https://data-nifc.opendata.arcgis.com/datasets/2020-perimeters-to-date
    """
    gpdList = []
    oldFireURL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Archived_Wildfire_Perimeters2/FeatureServer/0/query?where=CreateDate%20%3E%3D%20TIMESTAMP%20%27{}%2000%3A00%3A00%27%20AND%20CreateDate%20%3C%3D%20TIMESTAMP%20%27{}%2000%3A00%3A00%27%20AND%20GISAcres%20%3E%3D%205000%20AND%20GISAcres%20%3C%3D%201000000&outFields=*&outSR=4326&f=geojson"

    recursive_fire_data(oldFireURL, '2020-06-01', '2020-12-31', 12, gpdList)
            
    df = gpd.GeoDataFrame(
            pd.concat(gpdList, axis = 0, ignore_index = True),
            crs = gpdList[0].crs
            )
    print('size of unfiltered data', len(df))
    subset = gpd.sjoin(df, studyArea, 'inner', 'within')[colList]
    print('size of filtered data', len(subset))
    dissolved = subset.dissolve(by = 'IncidentName')
    dissolved['Area'] = dissolved.geometry.to_crs(epsg=3395).area
    dissolved.to_file('data/oldFireGPD.geojson', driver = 'GeoJSON')
    

# alternative using bounds of CA, OR, WA - not working due to timeout   
#chURL = "https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query?where=sciname+LIKE+%27%25%27&objectIds=&time=&geometry=%5B%5B-124.733174%2C+49.002494%5D%2C+%5B-114.134427%2C49.002494+%5D%2C+%5B-114.134427%2C+32.534156%5D%2C%5B-124.733174%2C+32.534156%5D%2C%5B-124.733174%2C+49.002494%5D%5D&geometryType=esriGeometryPolygon&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=&returnGeometry=true&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=geojson&token="
#chJson = requests.get(chURL).json()
#chGpd = gpd.GeoDataFrame.from_features(chJson['features'])
