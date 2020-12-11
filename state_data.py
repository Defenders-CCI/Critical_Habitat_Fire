# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 13:44:35 2020

@author: MEvans
"""
import requests
import zipfile
import os
#from os.path import basename
#from os import listdir

r = requests.get('https://www2.census.gov/geo/tiger/GENZ2019/kml/cb_2019_us_state_20m.zip')
with open('data/states.zip', 'wb') as fd:
    fd.write(r.content)

# unzip the downloaded states.zip file to kml
with zipfile.ZipFile('data/states.zip', 'r') as zip_ref:
    zip_ref.extractall('data')

# delete zip file
os.remove('data/states.zip')

#dataFiles = listdir('data')
#basenames = [basename(file) for file in dataFiles]

# enable kml driver

