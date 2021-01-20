# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 13:19:54 2020

@author: MEvans
"""
import geopandas as gpd

# Load our fire data
print('reading data')
firesPath = 'data/fireGPD.geojson'
oldFiresPath = 'data/oldFireGPD.geojson'
fireGpd = gpd.read_file(firesPath, driver = 'GeoJSON')
oldFireGpd = gpd.read_file(oldFiresPath , driver = 'GeoJSON')
chPath = 'data/chGPD.geojson'
chGpd = gpd.read_file(chPath, driver = 'GeoJSON').to_crs(epsg = 3395)

# merge all fire data and project
print('merging current and old fires')
merged = fireGpd.append(oldFireGpd).to_crs(epsg = 3395)

# unary union creates a union of all geometries in a geoseries
fireUnion = merged.geometry[merged.geometry.is_valid].unary_union
#chUnion = chGpd.geometry.buffer(0.1).unary_union
#
#area = chUnion.intersection(fireUnion).area
#
## create a series of buffer distances in km
#buffers = [round(10**(x/2)*1000) for x in list(range(0, 5, 1))]
#
## for each buffer distance, calculate burned area
#ys = [fxn.calc_burned_area(chUnion, fireUnion, x) for x in buffers]
#
#df = pd.DataFrame({'buffer': buffers})
#df['area']=df.apply(lambda row: fxn.calc_burned_area(chUnion, fireUnion, row.buffer))
#
## save as pandas dataframe
#df.to_csv('data/intersections.csv')
#print(area)

print('computing ch x burned intersection')
chGpd['burned'] = chGpd.geometry.buffer(0.1).intersection(fireUnion).area
print('writing to file')
chGpd.to_file('data/burned.geojson', driver = 'GeoJSON')
