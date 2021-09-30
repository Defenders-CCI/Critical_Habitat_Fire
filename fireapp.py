# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 11:02:47 2020

@author: MEvans
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import functions as fxn
import geopandas as gpd
import pandas as pd
import json
#import time
# https://inciweb.nwcg.gov/incident/7603/
# Load our fire data
firesPath = 'data/fireGDFsimple.geojson'
oldFiresPath = 'data/oldFireGDFsimple.geojson'
chPath = 'data/burnedCh.csv'
fireGpd = gpd.read_file(firesPath, driver = 'GeoJSON')
oldFireGpd = gpd.read_file(oldFiresPath , driver = 'GeoJSON')
fireJson = json.loads(open(firesPath, 'r').read())
oldFireJson = json.loads(open(oldFiresPath, 'r').read())
burned = pd.read_csv(chPath)

# Generate list of species w/designated CH in CA, OR, WA
codes = list(set(burned.spcode.tolist()))
#species = list(set(ranges.SCINAME.tolist()))
comnames = sorted(list(set(burned.comname.tolist())))
options = [{'label':'All species', 'value':''}]
options.extend([{'label': x, 'value': burned.spcode[burned.comname == x].values[0]} for x in comnames])

# fix species scinames with parentheses because this screws up downstream search and filtering
#ranges.SCINAME = [x.replace('(', '').replace(')', '') for x in ranges.SCINAME]
#burned.sciname = [x.replace('(', '').replace(')', '') for x in burned.sciname]

# Calculate total burned area in km2
totBurn = burned['burned'].sum()/1000000
burnText = 'Wildfire has burned in {:.2f} km\u00b2 of critical habitat in 2021'.format(totBurn)
# create the initial map of burned area and bar chart
fires = fxn.make_fire_map(fireJson, fireGpd, oldFireJson, oldFireGpd)
bars = fxn.make_bar_chart(burned)

# Create UI components
Map = dcc.Graph(
        id = 'map',
        figure = fires,
        config = {'responsive':True},
        style = {'height':'90vh'}
)

graph = dcc.Graph(
        id = 'bars',
        figure = bars,
        config = {'responsive':True},
        style = {'height':'90vh'}
)

dropdown = dcc.Dropdown(
        id = 'species_dropdown',
        options = options,
        style = {'color':'black'}
        )

alert = dbc.Alert(burnText,
                  style = {'backgroundColor':'orange', 'color':'#003B87'})

title = html.H2('Western U.S. Wildfire and ESA Critical Habitat')

explanation = html.P('This app calculates and displays the area burned by wildfire since June 2021 within the ranges and critical habitat of listed species in the Western US.',
                     style = {'marginTop':'12px'})

modalText = 'In fire-adapted ecosystems across the Western US, fire is a natural disturbance that positively shapes the landscape. '\
'Natural fires influence forest composition, structure, and pattern creating a mosaic of different seral stages supporting a rich array of biodiversity. '\
'However, anthropogenic factors related to timber management and climate change are creating wildfire that is more intense, extensive, and frequent than under historic regimes. '\
'These uncharacteristic wildfires can be problematic for imperiled species when they destroy necessary habitat.'
#'Big and old trees typically are able to withstand such fires and many fire-adapted wildlife species thrive in such conditions.'\

disclaimer = html.P(modalText, style = {'fontSize':'12px', 'marginTop':'12px'})

attribution = html.P([
        'Fire perimeters updated daily using ',
        html.A('National Interagency Fire Center data',
               href = 'https://data-nifc.opendata.arcgis.com/datasets/wildfire-perimeters',
               style = {'marginBottom':'12px', 'textAlign':'center'})
        ],
        style = {'backgroundColor':'white'})
                     
ecos = html.P([
        'Threatened & Endagered species range and critical habitat data provided by ',
        html.A('ECOS',
               href = 'https://ecos.fws.gov/ecp/',
               style = {'marginBottom':'12px', 'textAlign':'center'})
        ],
        style = {'backgroundColor':'white'})
                        
modal = html.Div(
        [#dbc.Button('Open modal', id = 'open'),
         dbc.Modal(
                 [dbc.ModalHeader("Wildfire & Wildlife"),
                  dbc.ModalBody(modalText),
                  dbc.ModalFooter(
                          dbc.Button('Close', id = 'close', className = 'ml-auto')
                          )
                  ], id = 'modal', is_open = True, keyboard = True
                 )
        ]
        )
                 
#box = html.Div(className = 'box', 
#               children = ['Total critical habitat burned', 'km<sup>2</sup>'],
#               style = {'textAlign': 'center',
#                        'backgroundColor': '#003B87',
#                        'color': '#f2f2f2'})

map_loader = dcc.Loading(
        id = 'loading-map',
        children = [Map])

graph_loader = dcc.Loading(
        id = 'loading-graph',
        children = [graph])

#app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP], requests_pathname_prefix = '/app/fireapp/', routes_pathname_prefix = '/app/fireapp/')
# for deployed version
app = dash.Dash(__name__, serve_locally = False, external_stylesheets = [dbc.themes.BOOTSTRAP], requests_pathname_prefix = '/app/fireapp/', routes_pathname_prefix = '/app/fireapp/')

app.layout = dbc.Container([
        modal,
        dbc.Row([title         
                ]),
        dbc.Row([
                dbc.Col([
#                        html.H3('About this app', style = {'color':'#333333'}),
                        explanation,
                        alert,
                        html.P('Select a species'),  
                        dropdown,                        

                        html.P('Wildfire & Wildlife', style = {'marginTop':'15px', 'marginBottom':'0px'}),
                        disclaimer
                        ],
                        width = 2,
                        className = 'section sidebar'),
                dbc.Col([graph_loader, ecos], width = 5),
                dbc.Col([map_loader, attribution], width = 5)
                        ])
                ], fluid = True)

        
@app.callback(
        [Output(component_id = 'map', component_property = 'figure'),
         Output(component_id = 'bars', component_property = 'figure')],
        [Input(component_id = 'species_dropdown', component_property = 'value')]
        )
def update_map(spcode):
    print(spcode)
    if(spcode in codes):
 
        # subset the burned critical habitat DataFrame by selected species code
        chSub = burned[burned.spcode == spcode]

#        chIndex = chSub.index.values
        
#        spp = sp.replace('(', '').replace(')','')
#        chSub = burned[burned.spcode.str.contains(spp)].reset_index()

#        rngSub = ranges[ranges.SCINAME.str.contains(spp)].reset_index()

        newMap = fxn.make_ch_map(chSub, fireJson, fireGpd, oldFireJson, oldFireGpd)
        newBar = fxn.make_species_bar(chSub.reset_index())
    else:
        newMap = fires
        newBar = bars
    return newMap, newBar

@app.callback(
        Output('modal', 'is_open'),
        [Input('close', 'n_clicks')],
        [State('modal', 'is_open')])
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

#@app.callback(
#        Output(component_id = "loading-output", component_property =  "children"),
#        [Input("loading", "value")]
#        )
#
#def input_triggers_spinner(value):
#    time.sleep(1)
#    return value

if __name__ == '__main__':
    app.run_server(debug=True)

# for deployed version
server = app.server

#if __name__ == '__main__':
#    app.run_server(host = '0.0.0.0', port = '5000')