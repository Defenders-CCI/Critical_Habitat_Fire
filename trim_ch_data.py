# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 14:19:50 2020

@author: MEvans

One-off file to create a west-coast geogrpahic subset of critical habitat, given the current file has
the complete inventory for all species
"""
import geopandas as gpd

chPath = 'data/chGPD.geojson'
chGpd = gpd.read_file(chPath, driver = 'GeoJSON').to_crs(epsg = 3395)

gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
statesGpd = gpd.read_file('data/cb_2019_us_state_20m.kml', driver = 'KML')

# Create a subset of west coast states and define projection
studyArea = statesGpd[statesGpd.Name.str.contains('California|Oregon|Washington')].to_crs(epsg = 3395)
chSubset = gpd.sjoin(chGpd, studyArea, 'inner', 'within')

chSubset.to_file(chPath, driver = 'GeoJSON')