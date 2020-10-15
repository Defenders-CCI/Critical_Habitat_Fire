# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 22:26:52 2020

@author: MEvans
"""
import functions as fxn
import geopandas as gpd

# get list of all species with CH in CA, OR, WA
species = list(fxn.get_species_list())
chGpd = gpd.GeoDataFrame()
# get the CH geojson for each species 1 by 1 to avoid timeout
for i in range(len(species)):
    spJson = fxn.get_ch_json([species[i]])
    spGpd = gpd.GeoDataFrame.from_features(spJson['features'])
    chGpd = chGpd.append(spGpd)

chGpd.to_file('data/chGPD.geojson', driver = 'GeoJSON')