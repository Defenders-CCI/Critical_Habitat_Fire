# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 14:03:14 2020

@author: MEvans
"""
import geopandas as gpd
import plotly.graph_objects as go
import requests
import numpy as np

# TODO: add ability to provide list of states
def get_species_list():
    url = "https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export?format=json&columns=%2Fspecies%40cn%2Csn%2Cstatus%2Cdesc%2Clisting_date&sort=%2Fspecies%40cn%20asc%3B%2Fspecies%40sn%20asc&filter=%2Fspecies%2Frange_state%40abbrev%20in%20('CA'%2C'OR'%2C'WA')&filter=%2Fspecies%2Fcrithab_docs%40crithab_status%20%3D%20'Final'"
    speciesJson = requests.get(url).json()
    speciesData = speciesJson['data']
    species = [x[1]['value'] for x in speciesData]
    species = np.unique(np.array(species))
    return species

def get_ch_json(species):
  url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query?where=sciname+IN+%28%27{}%27%29&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=sciname%2C+comname&returnGeometry=true&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
  # for a single species
#  sciname = '+'.join(species.split(" "))
  # for one in a list of species
  sciname = '%27%2C+%27'.join(['+'.join(sp.split(" ")) for sp in species])
  print(url.format(sciname))
  chRequest = requests.get(url.format(sciname))
  return chRequest.json()

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

def make_ch_map(sp, fireJson, fireGpd, oldFireJson, oldFireGpd):
    """
    Create a plotly map showing critical habitat for a species with 
    current fire and burned area data
    
    Parameters
    ----
    sp (str): scientific name of species
    fireJson (GeoJSON): object containing geometry of current fires
    fireGpd (GeoDataFrame): object containing geometry and attribute data of current fires
    oldFireJson (GeoJSON): object containing geometry of previously burned area
    oldFireGpd (GeoDataFrame): object containing geometry and attribute data of burned area
    
    Returns
    ----
    Plotly Figure: choropleth map showing species range boundaries, current fire footprints
        and previously burned area.
    """
    chJson = get_ch_json([sp])
    chGpd = gpd.GeoDataFrame.from_features(chJson)
    chGpd['count'] = 1
    center = chGpd.geometry.centroid
    bounds = chGpd.bounds
#   take a spatial subset of fire data near the species critical habitat
    subset = fireGpd.cx[bounds.minx[0]:bounds.maxx[0], bounds.miny[0]:bounds.maxy[0]]
    oldSubset = oldFireGpd.cx[bounds.minx[0]:bounds.maxx[0], bounds.miny[0]:bounds.maxy[0]]

    layout = go.Layout(mapbox_zoom = 6,
                      #getBoundsZoomLevel(bounds, {'height':500, 'width':1000}),
                      mapbox_center = {"lat": center.y[0], "lon": center.x[0]},
                      mapbox_style = "carto-positron",
                      legend = {'bordercolor': 'black',
                                'x':0.95,
                                'xanchor': 'right',
                                'y':0.95},
                     margin = {'r':15, 'l':15, 't':15, 'b':15})
    
    layer = go.Choroplethmapbox(
      geojson = chJson,
      locations = chGpd.comname,
      z = chGpd['count'],
      colorscale = ['green', 'green'],
      featureidkey = 'properties.comname',
      name = chGpd.comname.tolist()[0],
      marker = {'line':
                {'color':'green',
                 'width': 2}
      },
      showscale = False,
      showlegend = True
    )
    
    data = [layer]
    
    if len(oldSubset) > 0:

     layer1 = go.Choroplethmapbox(
        name = 'Burned 2020',
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
     
     data.append(layer1)

    if len(subset) > 0:

     layer2 = go.Choroplethmapbox( 
        # data_frame = fireGpd[['OBJECTID', 'IncidentName', 'GISAcres']],
        name = 'Current fires',
        geojson = fireJson,
        locations = subset.GlobalID,
        featureidkey = 'properties.GlobalID',
        z = round(subset.Area/1000000, 2),
#        colorscale = 'Hot',
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
    
     data.append(layer2)
  
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
            name = 'Burned 2020',
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
    
    layout = go.Layout(mapbox_zoom = 5,
                       mapbox_center = {"lat": 41.955, "lon": -120.073},
                       mapbox_style = "carto-positron",
                        legend = {'bordercolor': 'black',
                               'x':0.95,
                               'xanchor': 'right',
                               'y':0.95},
                        margin = {'r':15, 'l':15, 't':0, 'b':0})
    
    return go.Figure(data = [layer2, layer1], layout = layout)

def calc_burned_area(ch, fire, dist):
    """Calculate the burned area within given distance of critical habitat polygons
    @param ch {geometry}: critical habitat polygon union
    @param fire {geometry}: burned area polygon union
    @param dist {float}: distance
    @return {float}: acres of burned area
    """
    buffered = ch.buffer(dist)
    intersection = fire.intersection(buffered)
    area = intersection.area
    return area

# make a figure of burned area by species
def make_bar_chart(ch):
    """Create a plotly bar chart showing burned critical habitat by species
    @param ch {GeoDataFrame}:critical habitat data with burned area
    @return {plotly Figure}: bar chart figure
    """
    duplicates = [not x for x in ch.duplicated(['comname', 'burned'])]
    topTen = ch[duplicates & (ch.burned > 0)].sort_values(by = 'burned', ascending = False)#.iloc[0:10]
    
    burned = topTen.burned/1000000
    trace = go.Bar(
        y = topTen.comname,
        x = burned,
        text = burned,
        texttemplate = '%{text:.2f} km<sup>2</sup>',
        textposition = 'outside',
        orientation = 'h',
        hovertemplate = "%{y}<br>" + "%{x:.2f} km<sup>2</sup> burned",
        marker_color = 'blue')
    
    layout = go.Layout(xaxis = {'title':'Burned area (km<sup>2</sup>)'},
                       margin = {'r':15, 'l':15, 't':30, 'b':15},
                       title = {
                               'text':'Species w/Burned Critical Habitat',
                               'x': 0.5,
                               'xanchor': 'center'}
                       )
    
    fig = go.Figure(trace, layout)
    return fig

def make_species_bar(sp):
    """Create a bootstrap alert for a single species
    
    Parameters
    ---
    sp (GeoDataFrame): 
    
    Returns
    ---
    Plotly Figure
    """
    area = sp.area.sum()/1000000
    burn = sp.burned.sum()/1000000
    comname = sp.comname
    trace1 = go.Bar(
            x = [area-burn],
            y = comname,
            name = 'Unburned',
            orientation = 'h',
            marker_color = 'green',
            hovertemplate = "%{x:.2f} km<sup>2</sup> unburned critical habitat")
    
    trace2 = go.Bar(
            x = [burn],
            y = comname,
            name = 'Burned',
            orientation = 'h',
            marker_color = 'grey',
            hovertemplate = "%{x:.2f} km<sup>2</sup> burned critical habitat")
    
    layout = go.Layout(
            height = 300,
            xaxis={'title': 'Critical habitat area (km<sup>2</sup>)'},
            yaxis = {'showticklabels':False},
            title = '{}: {:.2f} km<sup>2</sup> ({:.1f}%) burned'.format(comname[0], burn, (burn/area)*100),
            barmode = 'stack')
    
    fig = go.Figure(data = [trace1, trace2], layout = layout)
    return fig
    