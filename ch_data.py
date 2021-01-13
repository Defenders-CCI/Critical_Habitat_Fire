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
 
# read in state data, native projection is 4326
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
statesGpd = gpd.read_file('data/cb_2019_us_state_20m.kml', driver = 'KML')

# Create a subset of west coast states and define projection
studyArea = statesGpd[statesGpd.Name.str.contains('California|Oregon|Washington')]
ch = chGpd.set_crs(epsg = 4326)

chSubset = gpd.sjoin(ch, studyArea, 'inner', 'within')[['comname', 'geometry', 'sciname']]

chSubUnique = chSubset.dissolve(by = 'sciname')

chSubUnique.to_file('data/chGPD.geojson', driver = 'GeoJSON')
