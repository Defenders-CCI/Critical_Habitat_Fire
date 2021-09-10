# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 14:03:14 2020

@author: MEvans
"""
import geopandas as gpd
from shapely import wkt
import plotly.graph_objects as go
import requests
import numpy as np
import urllib
import json

def wkt_to_json(df):
    df['geometry'] = gpd.GeoSeries.from_wkt(df['wkt'])
    gdf = gpd.GeoDataFrame(df, geometry = 'geometry')
    js = json.loads(gdf.to_json())
    return js

def write_wkt(gdf, path):
    gdf['wkt'] = gdf.geometry.to_wkt()
#    epsg = gdf.crs.to_epsg()
#    gdf['epsg'] = epsg
    gdf.drop('geometry', axis = 1).to_csv(path)

# TODO: add ability to provide list of states
def get_species_list():
    url = "https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export?format=json&columns=%2Fspecies%40cn%2Csn%2Cstatus%2Cdesc%2Clisting_date&sort=%2Fspecies%40cn%20asc%3B%2Fspecies%40sn%20asc&filter=%2Fspecies%2Frange_state%40abbrev%20in%20('CA'%2C'OR'%2C'WA')&filter=%2Fspecies%2Fcrithab_docs%40crithab_status%20%3D%20'Final'"
    speciesJson = requests.get(url).json()
    speciesData = speciesJson['data']
    species = [x[1]['value'] for x in speciesData]
    species = np.unique(np.array(species))
    return species

def get_range_envelope(sp):
    """
    Return the bounding box tuple for a species range from ECOS
    Params:
        sp (str): acientific name used to identify species in ECOS
    Return:
        tpl: (minx, miny, maxx, maxy)
    """
    url = 'https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export'
    species_unencoded = f"/species@sn = '{sp}'"
    
    params = {
            'format':'json',
            'columns':'/species@cn,sn,id,range_envelope',
            'sort':'/species@cn asc;/species@sn asc',
            #'filter':species_unencoded,
            'filter':"/species@status in ('Endangered','Threatened')"}
    # urllbi doesn't handle dictionaries with two of the same key, so we combine filters manually
    payload = urllib.parse.urlencode(params, quote_via=urllib.parse.quote) + '&filter=' + urllib.parse.quote(species_unencoded)
    request = requests.get(url, params = payload)
    js = request.json()
    envelope = wkt.loads(js['data'][0][3])
    series = gpd.GeoSeries(envelope, crs = 'EPSG:4269') #FWS doesn't give metadata for envelopes. Ranges provided in 4269
    bounds = series.geometry[0].bounds
    return bounds
#    coord_string = envelope.replace('POLYGON((', '').replace('))', '')
#    coord_string_pairs = coord_string.split(sep = ',')
#    coords = [[float(coord) for coord in pair.split(sep = ' ')] for pair in coord_string_pairs]
#    return (coords[0][0], coords[0][1], coords[2][0], coords[2][1], js)

def get_ch_json(spcode):
    url = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query'
    spcode_query = f"spcode='{spcode}'"
    params = {
            'f':'geojson',
            'returnGeometry':'true',
            'outFields':'comname,sciname,spcode',
            'where':spcode_query}
#    outFields=comname%2C+sciname%2C+spcode
    payload = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    request = requests.get(url, params = payload)
    js = request.json()
    return js
    

#def get_ch_json(species):
#  url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query?where=sciname+IN+%28%27{}%27%29&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=sciname%2C+comname&returnGeometry=true&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
#  # for a single species
##  sciname = '+'.join(species.split(" "))
#  # for one in a list of species
#  sciname = '%27%2C+%27'.join(['+'.join(sp.split(" ")) for sp in species])
#  print(url.format(sciname))
#  chRequest = requests.get(url.format(sciname))
#  return chRequest.json()

def get_range_json(index):
    gdf = gpd.read_file('data/rangeGPD.shp', ignore_fields = ['STATUS_ABB', 'Area'], rows = slice(index, index+1)).to_crs(epsg = 4326)
#    bbox = get_range_envelope(sp)
#    gdf = gpd.read_file('data/rangeGPD.shp', bbox = bbox).to_crs(epsg = 4326)
#    gdf = gdf[gdf.SPCODE == spcode]
    js = json.loads(gdf.to_json())
    return gdf, js

def getBoundsZoomLevel(bounds, mapDim):
    """
    source: https://stackoverflow.com/questions/6048975/google-maps-v3-how-to-calculate-the-zoom-level-for-a-given-bounds
    :param bounds: list of ne and sw lat/lon
    :param mapDim: dictionary with image size in pixels
    :return: zoom level to fit bounds in the visible area
    """
    ne_lat = bounds.maxy[0]
    ne_long = bounds.minx[0]
    sw_lat = bounds.miny[0]
    sw_long = bounds.maxx[0]

    # scale = 2 # adjustment to reflect MapBox base tiles are 512x512 vs. Google's 256x256
    WORLD_DIM = {'height': 512, 'width': 512}
    ZOOM_MAX = 18

    def latRad(lat):
        sin = np.sin(lat * np.pi / 180)
        radX2 = np.log((1 + sin) / (1 - sin)) / 2
        return max(min(radX2, np.pi), -np.pi) / 2

    def zoom(mapPx, worldPx, fraction):
        return np.floor(np.log(mapPx / worldPx / fraction) / np.log(2))

    latFraction = (latRad(ne_lat) - latRad(sw_lat)) / np.pi

    lngDiff = ne_long - sw_long
    lngFraction = ((lngDiff + 360) if lngDiff < 0 else lngDiff) / 360

    latZoom = zoom(mapDim['height'], WORLD_DIM['height'], latFraction)
    lngZoom = zoom(mapDim['width'], WORLD_DIM['width'], lngFraction)

    return min(latZoom, lngZoom, ZOOM_MAX)

def make_ch_map(rngindex, chSub, fireJson, fireGpd, oldFireJson, oldFireGpd):
    """
    Create a plotly map showing critical habitat for a species with 
    current fire and burned area data
    
    Parameters
    ----
    spcode (str): ECOS species identifier
    fireJson (GeoJSON): object containing geometry of current fires
    fireGpd (GeoDataFrame): object containing geometry and attribute data of current fires
    oldFireJson (GeoJSON): object containing geometry of previously burned area
    oldFireGpd (GeoDataFrame): object containing geometry and attribute data of burned area
    
    Returns
    ----
    Plotly Figure: choropleth map showing species range boundaries, current fire footprints
        and previously burned area.
    """
    rngGdf, rngJson = get_range_json(rngindex)
    rngGdf['count'] = 1,
#    rngJson = wkt_to_json(rng)
    center = rngGdf.geometry[0].centroid
    bounds = rngGdf.geometry[0].bounds
    
#    chGpd = gpd.read_file('data/chGPD.geojson', driver = 'GeoJSON', bbox = bounds)
#    chGpd = chGpd[chGpd.spcode == spcode].reset_index()
    
#   take a spatial subset of fire data near the species critical habitat
    subset = fireGpd.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
    oldSubset = oldFireGpd.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]

    layout = go.Layout(mapbox_zoom = 6,
                      #getBoundsZoomLevel(bounds, {'height':500, 'width':1000}),
                      mapbox_center = {"lat": center.y, "lon": center.x},
                      mapbox_style = "carto-positron",
                      legend = {'bordercolor': 'black',
                                'x':0.95,
                                'xanchor': 'right',
                                'y':0.95},
                     margin = {'r':15, 'l':15, 't':15, 'b':15})
    
    layer = go.Choroplethmapbox(
            geojson = rngJson,
            locations = rngGdf.COMNAME,
            z = rngGdf['count'],
            colorscale = ['purple', 'purple'],
            featureidkey = 'properties.COMNAME',
            name = f'{rngGdf.COMNAME.tolist()[0]} range',
            marker = {'line':{'color':'purple', 'width':2}},
            showscale = False,
            showlegend = True)
    
    data = [layer]
    
    if len(chSub) > 0:
        # first try pulling critical habitat spatial data from the web server
        chindex = chSub.index.values[0]
        chcode = chSub.spcode.values[0]
        
        try:
            chJson = get_ch_json(chcode)
            chGdf = gpd.GeoDataFrame.from_features(chJson)
        # if that fails, as it will for big files, get the relevant row from local data
        except:
            print('failed to get CH data from ECOS')
            chGdf = gpd.read_file('data/chGPD.shp', ignore_fields = ['GlobalID', 'OBJECTID_1', 'Shape__Area', 'status', 'effectdate'], rows = slice(chindex, chindex+1))
            
        chGdf['count'] = 1
        chJson = json.loads(chGdf.to_json())
        
        layer1 = go.Choroplethmapbox(
          geojson = chJson,
          locations = chGdf.comname,
          z = chGdf['count'],
          colorscale = ['green', 'green'],
          featureidkey = 'properties.comname',
          name = f'{chGdf.comname.tolist()[0]} CH',
          marker = {'line':
                    {'color':'green',
                     'width': 2}
          },
          showscale = False,
          showlegend = True
        )
        
        data.append(layer1)
    
    if len(oldSubset) > 0:

        layer2 = go.Choroplethmapbox(
           name = 'Burned 2021',
           geojson = oldFireJson,
           locations = oldSubset.GlobalID,
           featureidkey = 'properties.GlobalID',
           z = round(oldSubset.Area/1000000, 2),
           text = subset.IncidentName,
           hovertemplate = "Name: %{text}<br>" + "Area: %{z} km<sup>2</sup>",
           colorscale = ['#a5a5a5', '#a5a5a5'],
           marker = {'line':{'color':'black', 'width':2}},
           showlegend = True,
           showscale = False
           )
         
        data.append(layer2)

    if len(subset) > 0:

        layer3 = go.Choroplethmapbox( 
           # data_frame = fireGpd[['OBJECTID', 'IncidentName', 'GISAcres']],
           name = 'Current fires',
           geojson = fireJson,
           locations = subset.GlobalID,
           featureidkey = 'properties.GlobalID',
           z = round(subset.Area/1000000, 2),
        #       colorscale = 'Hot',
           colorscale = ['orange', 'orange'],
           text = subset.IncidentName,
           hovertemplate = "Name: %{text}<br>" + "Area: %{z} km<sup>2</sup>",
           showlegend = True,
           showscale = False,
           colorbar = {
               'x':0,
               'title':{
                   'text':'Burned km2'
               }
           }
           )
        
        data.append(layer3)
  
    return go.Figure(data = data, layout = layout)

def make_fire_map(fireJson, fireGpd, oldFireJson, oldFireGpd):

    layer1 = go.Choroplethmapbox(
            name = 'Current fires',
            geojson = fireJson,
            locations = fireGpd.GlobalID,
            featureidkey = 'properties.GlobalID',
            z = round(fireGpd.Area/1000000, 2),
#            colorscale = 'Hot',
            colorscale = ['orange', 'orange'],
            text = fireGpd.IncidentName,
            hovertemplate = "Name: %{text}<br>" + "Area: %{z} km<sup>2</sup>",
            showlegend = True,
            showscale = False,
            colorbar = {
                    'x':0,
                    'title':{
                            'text':'Burned km2'}
                    }
    )
    
    layer2 = go.Choroplethmapbox(
            name = 'Burned 2021',
            geojson = oldFireJson,
            locations =oldFireGpd.GlobalID,
            featureidkey = 'properties.GlobalID',
            z = round(oldFireGpd.Area/1000000, 2),
            colorscale = ['#a5a5a5', '#a5a5a5'],
            text = oldFireGpd.IncidentName,
            hovertemplate = "Name: %{text}<br>" + "Area: %{z} km<sup>2</sup>",
            marker = {'line':{'color':'black', 'width':2}},
            showscale = False,
            showlegend = True
    )
    
    layout = go.Layout(mapbox_zoom = 4,
                       mapbox_center = {"lat": 41.955, "lon": -120.073},
                       mapbox_style = "carto-positron",
                        legend = {'bordercolor': 'black',
                               'x':0.95,
                               'xanchor': 'right',
                               'y':0.95},
                        margin = {'r':15, 'l':15, 't':15, 'b':15},
                        autosize = True)
    
    return go.Figure(data = [layer2, layer1], layout = layout)

def calc_burned_area(ch, fire, dist):
    """Calculate the burned area within given distance of critical habitat polygons
    Parameters:
        ch {geometry}: critical habitat polygon union
        fire {geometry}: burned area polygon union
        dist {float}: distance
    Return:
        float: acres of burned area
    """
    buffered = ch.buffer(dist)
    intersection = fire.intersection(buffered)
    area = intersection.area
    return area

# make a figure of burned area by species
def make_bar_chart(ch, ranges):
    """Create a plotly bar chart showing burned critical habitat by species
    Parameters:
        ch (GeoDataFrame):critical habitat data with burned area
        ranges (GeoDataFrame):species range data with burned area
    Return:
        plotly Figure: bar chart figure
    """
    # First process critical habitat burn data
    ch['percent'] = (ch.burned/ch.Area)*100
    duplicates = [not x for x in ch.duplicated(['comname', 'burned'])]
    topTen = ch[duplicates & (ch.burned > 0)].sort_values(by = 'burned', ascending = False).iloc[0:20]
    
    burned = topTen.burned/1000000
    maxburn = max(burned)
    chTrace = go.Bar(
        y = topTen.comname,
        x = burned,
        name = 'Burned CH',
        text = topTen.percent,
        texttemplate = '%{x:.2f} km<sup>2</sup> (%{text:.2f}%)',
        textposition = 'outside',
        orientation = 'h',
        hovertemplate = "%{y}<br>" + "%{x:.2f} km<sup>2</sup> burned<br>" + "%{text:.2f}% of critical habitat",
        marker_color = 'black')
    
    #Now process range data
    ranges['percent'] = (ranges.burned/ranges.Area)*100
    duplicates = [not x for x in ranges.duplicated(['COMNAME', 'burned'])]
    topTen = ranges[duplicates & (ranges.burned >0)].sort_values(by = 'burned', ascending = False).iloc[0:20]
    burned = topTen.burned/1000000
    maxburn = max(burned)
    
    rangeTrace = go.Bar(
        y = topTen.COMNAME,
        x = burned,
        name = 'Burned range',
        text = topTen.percent,
        texttemplate = '%{x:.2f} km<sup>2</sup> (%{text:.2f}%)',
        textposition = 'outside',
        orientation = 'h',
        hovertemplate = "%{y}<br>" + "%{x:.2f} km<sup>2</sup> burned<br>" + "%{text:.2f}% of range",
        marker_color = 'grey')
    
    layout = go.Layout(
            barmode = 'overlay',
            xaxis = {
                    'title':'Burned area (km<sup>2</sup>)',
                    'showgrid':False,
                    'range':[0, maxburn+(maxburn*0.1)]
                    },
            yaxis = {'tickfont':{'size':8}},
            margin = {'r':15,
                      'l':15, 
                      't':30,
                      'b':15},
                      
            #height = 300,
            title = {
                    'text':'Burned Critical Habitat',
                    'x': 0.5,
                    'xanchor': 'center'
                    },
            legend = {
                    'x':0.5,
                    'y':0.95},
            plot_bgcolor='rgba(0,0,0,0)'
            )
    
    fig = go.Figure([rangeTrace, chTrace], layout)
    return fig

def make_species_bar(ch, rng):
    """Create a bootstrap alert for a single species
    
    Parameters
    ---
    ch (GeoDataFrame):
    rng (GeoDataFrame):
    
    Returns
    ---
    Plotly Figure
    """
    
    rngArea = rng.Area.sum()/1000000
    rngBurn = rng.burned.sum()/1000000
    comname = rng.COMNAME
    
    trace1 = go.Bar(
            y = [rngArea],
            x = ['Range'],
            name = 'Range',
#            orientation = 'h',
            marker_color = 'purple',
            showlegend = True,
            hovertemplate = "%{y:.2f} km<sup>2</sup> unburned range")
    
    trace2 = go.Bar(
            y = [rngBurn],
            x = ['Range'],
            name = 'Burned', 
            text = rngBurn/rngArea,
            texttemplate = '%{y:.2f} km<sup>2</sup> (%{text:.2f}%) burned',
            textposition = 'outside',
            textfont_color = 'white',
#            orientation = 'h',
            marker_color = 'grey',
            hovertemplate = "%{y:.2f} km<sup>2</sup> burned range")
    
    data = [trace1, trace2]
    
    if len(ch) > 0:
        chArea = ch.Area.sum()/1000000
        chBurn = ch.burned.sum()/1000000
        
        trace3 = go.Bar(
                y = [chArea],
                x = ['Critical habitat'],
                name = 'Critical habitat',
#                orientation = 'h',
                marker_color = 'green',
                showlegend = True,
                hovertemplate = "%{y:.2f} km<sup>2</sup> unburned critical habitat")
        
        trace4 = go.Bar(
                y = [chBurn],
                x = ['Critical habitat'],
                name = 'Burned CH',
                text = chBurn/chArea,
                texttemplate = '%{y:.2f} km<sup>2</sup> (%{text:.2f}%) burned',
                textposition = 'outside',
                textfont_color = 'white',
#                orientation = 'h',
                marker_color = 'black',
                showlegend = True,
                hovertemplate = "%{y:.2f} km<sup>2</sup> burned critical habitat")
        
        data.append(trace3)
        data.append(trace4)
    
    layout = go.Layout(
            yaxis={'title': 'Area (km<sup>2</sup>)'},
            xaxis = {'showticklabels':True},
            title = f'{comname[0]}',
#            title = '{}: {:.2f} km<sup>2</sup> ({:.1f}%) burned'.format(comname[0], rngBurn, (rngBurn/rngArea)*100),
            barmode = 'overlay',
            legend = {'x':0.6, 'y':1},
            plot_bgcolor='rgba(0,0,0,0)')
    
    fig = go.Figure(data = data, layout = layout)
    return fig
    