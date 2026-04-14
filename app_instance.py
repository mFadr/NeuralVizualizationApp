# app_instance.py — just this, nothing else
import os
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server