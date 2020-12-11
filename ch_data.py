# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 22:26:52 2020

@author: MEvans
"""
import functions as fxn
import geopandas as gpd
import requests

# get list of all species with CH in CA, OR, WA
species = list(fxn.get_species_list())
chGpd = gpd.GeoDataFrame()
# get the CH geojson for each species 1 by 1 to avoid timeout
for i in range(len(species)):
    spJson = fxn.get_ch_json([species[i]])
    spGpd = gpd.GeoDataFrame.from_features(spJson['features'])
    chGpd = chGpd.append(spGpd)
 
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
statesGpd = gpd.read_file('data/cb_2019_us_state_20m.kml', driver = 'KML')

# Create a subset of west coast states and define projection
studyArea = statesGpd[statesGpd.Name.str.contains('California|Oregon|Washington')].to_crs(epsg = 3395)
chSubset = gpd.sjoin(chGpd, studyArea, 'inner', 'within')

chSubset.to_file('data/chGPD.geojson', driver = 'GeoJSON')
