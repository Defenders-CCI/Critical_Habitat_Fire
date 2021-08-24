# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 13:19:54 2020

@author: MEvans
"""
import geopandas as gpd
import pandas as pd
from time import time

# Load our fire data
print('reading fire data')
start = time()
firesPath = 'data/fireGPD.geojson'
oldFiresPath = 'data/oldFireGPD.geojson'
fireGpd = gpd.read_file(firesPath, driver = 'GeoJSON')
oldFireGpd = gpd.read_file(oldFiresPath , driver = 'GeoJSON')
end = time()
print(f'reading fire data took {(end-start)}s')

# merge all fire data and project
print('merging current and old fires')
start = time()
merged = fireGpd.append(oldFireGpd).to_crs(epsg = 3395)
# unary union creates a union of all geometries in a geoseries
fireUnion = merged.geometry[merged.geometry.is_valid].unary_union
del merged
end = time()
print(f'merging fire data took {(end-start)}s')

print('reading ch data')
start = time()
chPath = 'data/chGPD.geojson'
chGpd = gpd.read_file(chPath, driver = 'GeoJSON').to_crs(epsg = 3395)
end = time()
print(f'reading ch data took {(end-start)}s')


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
start = time()
chGpd['burned'] = chGpd.geometry.buffer(0.1).intersection(fireUnion).area
end = time()
print(f'computing ch x burned intersection took {(end-start)}s')
print('writing burned ch to file')
chGpd.drop('geometry', axis = 1).to_csv('data/burnedCh.csv')
del chGpd

print('reading range data')
start = time()
rangePath = 'data/rangeGPD.shp'
rangeGpd = gpd.read_file(rangePath).to_crs(epsg = 3395)
end = time()
print(f'reading range data took {(end-start)}s')

print('computing range x burned intersection')
start = time()
rangeGpd['burned'] = rangeGpd.geometry.buffer(0.1).intersection(fireUnion).area
end = time()
print(f'computing range x burned intersection took {(end-start)}s')
print('writing burned ranges to file')
rangeGpd.drop('geometry', axis = 1).to_csv('data/burnedRanges.csv')
