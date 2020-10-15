# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 16:25:11 2020

@author: MEvans
"""

import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("CCI", href="https://www.defenders-cci.org")),
        dbc.NavItem(dbc.NavLink("GitHub", href = 'https://www.github.com/mjevans26')),
        dbc.NavItem(dbc.NavLink(dbc.'fa fa-question-circle fa-lg', href = 'mailto:mevans@defenders.org?subject=Fires&CH'))
    ],
    brand="West Coast Fires & Critical Habitat",
    brand_href="#",
    color="primary",
    dark=True,
)