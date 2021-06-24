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
import json
#import time

# Load our fire data
firesPath = 'data/fireGPD.geojson'
oldFiresPath = 'data/oldFireGPD.geojson'
chPath = 'data/burned.geojson'
fireGpd = gpd.read_file(firesPath, driver = 'GeoJSON')
oldFireGpd = gpd.read_file(oldFiresPath , driver = 'GeoJSON')
fireJson = json.loads(open(firesPath, 'r').read())
oldFireJson = json.loads(open(oldFiresPath, 'r').read())
burned = gpd.read_file(chPath, driver = 'GeoJSON')

# Generate list of species w/designated CH in CA, OR, WA
species = list(set(burned.sciname.tolist()))
comnames = sorted(list(set(burned.comname.tolist())))
options = [{'label':'All species', 'value':''}]
options.extend([{'label': x, 'value': burned.sciname[burned.comname == x].values[0]} for x in comnames])

# Calculate total burned area in km2
totBurn = burned['burned'].sum()/1000000
burnText = '{:.2f} km\u00b2 of critical habitat burned'.format(totBurn)
# create the initial map of burned area and bar chart
fires = fxn.make_fire_map(fireJson, fireGpd, oldFireJson, oldFireGpd)
bars = fxn.make_bar_chart(burned)

# Create UI components
Map = dcc.Graph(
        id = 'map',
        figure = fires,
#        style = {'height':500, 'width':1000}
)

graph = dcc.Graph(
        id = 'bars',
        figure = bars#,
#        style = {'height':300, 'width': 500}
)

dropdown = dcc.Dropdown(
        id = 'species_dropdown',
        options = options,
        style = {'color':'black'}
        )

alert = dbc.Alert(burnText,
                  style = {'backgroundColor':'orange', 'color':'#003B87'})

title = html.H2('Western U.S. Wildfire and ESA Critical Habitat')

explanation = html.P('This app calculates and displays the amount of designated critical habitat that has been burned by wildfire in CA, OR, & WA since June 2020.')

modal = html.Div(
        [#dbc.Button('Open modal', id = 'open'),
         dbc.Modal(
                 [dbc.ModalHeader("Wildfire & Wildlife"),
                  dbc.ModalBody('Wildfire is not always detrimental to wildlife, and fires are part of the natural cycle of many ecosystems.\
                                For species like X,Y,&Z that inhabit early successional habitat, fire is necessary to create new habitat.\
                                Fires that burn hotter, longer, and larger areas than historically are a threat to species if they eliminate a substantial portion of existing habitat,\
                                or burn habitat that is not easily restored, like old growth forest.'),
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

#loading = dcc.Loading(
#        id = 'loading',
#        children = html.Div(graph))

app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
        modal,
        dbc.Row([title         
                ]),
        dbc.Row([
                dbc.Col([
                        html.H3('About this app', style = {'color':'#333333'}),
                        explanation,
                        alert,
                        html.P('Select a species'),
                        dropdown,
                        html.A('Fire data updated daily using Interagency Fire Data', href = 'https://data-nifc.opendata.arcgis.com/datasets/wildfire-perimeters')
                        ],
                        width = 3,
                        className = 'section sidebar'),
                dbc.Col([graph, Map], width = 9)
                        ])
                ], fluid = True)

        
@app.callback(
        [Output(component_id = 'map', component_property = 'figure'),
         Output(component_id = 'bars', component_property = 'figure')],
        [Input(component_id = 'species_dropdown', component_property = 'value')]
        )
def update_map(sp):
    if(sp in species):
        subset = burned[burned.sciname.str.contains(sp)].reset_index()
        newMap = fxn.make_ch_map(sp, fireJson, fireGpd, oldFireJson, oldFireGpd)
        newBar = fxn.make_species_bar(subset)
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