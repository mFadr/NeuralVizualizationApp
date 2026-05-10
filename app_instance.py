import os
from dash import Dash

# app_instance.py — vytváří jedinou instanci Dash aplikace, sdílenou všemi moduly
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    # Tento řádek načte češtinu pro všechny grafy v aplikaci
    external_scripts=["https://cdn.plot.ly/plotly-locale-cs-latest.js"]
)

server = app.server
