import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import io
import sys

# CSV file paths mapped to origin codes

from config import DATASET_PATHS
# =====================================================================
# 1️⃣ Function: Load CSV data from file
# =====================================================================
def load_data_from_file(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")

    # Clean price
    df["price"] = df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)

    # Ensure expected columns exist
    for col in ["departure_time", "duration", "Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col not in df.columns:
            df[col] = None

    # Convert departure_time
    if "departure_time" in df.columns and df["departure_time"].notna().any():
        def normalize_time(time_str):
            if pd.isna(time_str):
                return time_str
            time_str = str(time_str).strip()
            if "AM" in time_str.upper() or "PM" in time_str.upper():
                try:
                    parsed_time = pd.to_datetime(time_str, format="%I:%M %p", errors="coerce")
                    if pd.notna(parsed_time):
                        return parsed_time.strftime("%H:%M")
                except:
                    pass
            return time_str

        df["departure_time"] = df["departure_time"].apply(normalize_time)

    # Convert to datetime
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")

    # Clean airline name
    df["airline"] = df["airline_details"].astype(str).str.strip()

    # Parse CO2 data - handle various formats
    for col in ["Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    # Rename columns
    df.rename(
        columns={
            "flight_date": "Date",
            "origin": "Origin",
            "destination": "Destination",
            "price": "Price",
            "airline": "Airline",
            "departure_time": "DepartureTime",
            "duration": "Duration",
            "Est. CO2 (kg)": "EstCO2",
            "AVG CO2 (kg/hr)": "AvgCO2"
        },
        inplace=True,
    )

    return df

# =====================================================================
# 2️⃣ Theme Configuration (Cyberpunk Style)
# =====================================================================
# Color Palette
BG_COLOR = "#0b0c10"        # Deep void black
GWHITE = "#F8F8FF"             # Light gray for text and gridlines
PANEL_BG = "#1f2833"        # Dark gray for panels
NEON_CYAN = "#66fcf1"       # Primary text/accents
NEON_BLUE = "#45a29e"       # Secondary accents
NEON_PINK = "#ff007f"       # Contrast color for charts
TEXT_MUTED = "#c5c6c7"      # Muted text
DROPDOWN_STYLE = {"color": "black", "marginBottom": "15px"} # Dropdowns need dark text to be readable without complex CSS

# New colors for horizontal bar charts
TRUE_PURPLE = "#9D4EDD"      # 1st chart
ELECTRIC_PURPLE = "#7209B7"  # 2nd chart
CHART_CYAN = "#00D9FF"       # 3rd chart

# =====================================================================
# 3️⃣ Dash App Setup (Layout + Callback)
# =====================================================================
from app_instance import app # share the single server instance
server = app.server

# Layout: Using Flexbox instead of hard floats and margins
layout = html.Div([
    html.H2(
        "✈️ NEURAL FLIGHT TRACKER v2.0 - MULTI-ORIGIN",
        style={
            "textAlign": "center",
            "textShadow": f"0 0 10px {NEON_CYAN}",
            "letterSpacing": "3px",
            "marginBottom": "30px"
        }
    ),

    # Main Container
    html.Div([


        # Back button — paste as first child of the layout Div
        html.A(
            "← BACK TO MAIN",
            href="/",
            style={
                "display": "inline-block",
                "color": "#66fcf1",
                "border": "1px solid #45a29e",
                "padding": "6px 16px",
                "borderRadius": "6px",
                "textDecoration": "none",
                "fontSize": "11px",
                "letterSpacing": "2px",
                "marginBottom": "1100px",
                "fontFamily": "Courier New, monospace",
                "backgroundColor": "#1f2833"
            }
        ),

        # 🎛️ LEFT PANEL: Filters
        html.Div([
            html.H3("SYSTEM PARAMETERS", style={"color": NEON_BLUE, "borderBottom": f"1px solid {NEON_BLUE}", "paddingBottom": "10px"}),

            # Filters Chart 1
            html.Div([
                html.H4("TRACKER ALPHA", style={"color": NEON_CYAN, "marginTop": "20px"}),
                html.Label("Dataset Origin"),
                dcc.Dropdown(
                    id="dataset-origin-1",
                    options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                    value="PRG",
                    style=DROPDOWN_STYLE
                ),
                html.Label("Destination"),
                dcc.Dropdown(id="destination-filter-1", value="AMS", style=DROPDOWN_STYLE),
                html.Label("Airline"),
                dcc.Dropdown(id="airline-filter-1", value="All", style=DROPDOWN_STYLE),
                html.Label("Search Date"),
                dcc.Dropdown(id="search-date-filter-1", value="All", style=DROPDOWN_STYLE)
            ], style={"border": f"1px solid {NEON_CYAN}", "padding": "15px", "borderRadius": "10px", "marginBottom": "20px", "boxShadow": f"0 0 10px {NEON_CYAN}40"}),

            # Filters Chart 2
            html.Div([
                html.H4("TRACKER BETA", style={"color": NEON_PINK}),
                html.Label("Dataset Origin"),
                dcc.Dropdown(
                    id="dataset-origin-2",
                    options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                    value="PRG",
                    style=DROPDOWN_STYLE
                ),
                html.Label("Destination"),
                dcc.Dropdown(id="destination-filter-2", value="FCO", style=DROPDOWN_STYLE),
                html.Label("Airline"),
                dcc.Dropdown(id="airline-filter-2", value="All", style=DROPDOWN_STYLE),
                html.Label("Search Date"),
                dcc.Dropdown(id="search-date-filter-2", value="All", style=DROPDOWN_STYLE)
            ], style={"border": f"1px solid {NEON_PINK}", "padding": "15px", "borderRadius": "10px", "boxShadow": f"0 0 10px {NEON_PINK}40"})

        ], style={
            "width": "25%",
            "backgroundColor": PANEL_BG,
            "padding": "20px",
            "borderRadius": "15px",
            "boxShadow": f"0 0 20px {NEON_BLUE}60",
            "height": "fit-content"
        }),

        # 📈 RIGHT PANEL: Charts
        html.Div([

            # Chart 1 Container
            html.Div([
                dcc.Graph(id="price-chart-1")
            ], style={"borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_CYAN}80", "marginBottom": "30px"}),

            # Chart 2 Container
            html.Div([
                dcc.Graph(id="price-chart-2")
            ], style={"borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_PINK}80"})

        ], style={"width": "75%", "display": "flex", "flexDirection": "column"})

    ], style={"display": "flex", "gap": "30px"}),

    # 📊 BOTTOM HORIZONTAL BAR CHARTS (3 in one line)
    html.Div([
        # Chart 3: 10 Cheapest Routes
        html.Div([
            html.Div([
                html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist-cheapest",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                ),
            ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
            dcc.Graph(id="cheapest-routes-chart")
        ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {TRUE_PURPLE}80"}),

        # Chart 4: 10 Most Expensive Routes
        html.Div([
            html.Div([
                html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist-expensive",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                ),
            ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
            dcc.Graph(id="expensive-routes-chart")
        ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {ELECTRIC_PURPLE}80"}),

        # Chart 5: Origin Airport Comparison with filters
        html.Div([
            html.Div([
                html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                ),
            ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
            dcc.Graph(id="origin-comparison-chart")
        ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {CHART_CYAN}80"})

    ], style={"display": "flex", "gap": "20px", "marginTop": "30px"})

], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "30px",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
})

# =====================================================================
# 4️⃣ Callbacks & Chart Styling
# =====================================================================
# Define allowed airlines mapping (IATA code to full name)
ALLOWED_AIRLINES = {
    'BA': 'British Airways',
    'FR': 'Ryanair',
    'KL': 'KLM',
    'LO': 'LOT',
    'OS': 'Austrian Airlines',
    'QS': 'Smartwings',
    'RK': 'Ryanair UK',
    'U2': 'EasyJet',
    'VY': 'Vueling',
    'W4': 'Wizz Air',
    'W6': 'Wizz Air',
    'W9': 'Wizz Air'
}

def filter_allowed_airlines(available_airlines):
    """Filter airlines to only include those in the ALLOWED_AIRLINES list"""
    filtered = []
    for airline in available_airlines:
        if pd.isna(airline):
            continue
        airline = str(airline).strip()
        if not airline:
            continue
        # Check if airline matches any code or full name in ALLOWED_AIRLINES
        airline_upper = airline.upper()
        if airline in ALLOWED_AIRLINES or airline in ALLOWED_AIRLINES.values():
            filtered.append(airline)
        # Also check if airline contains the code or name
        elif any(code in airline_upper for code in ALLOWED_AIRLINES.keys()):
            filtered.append(airline)
        elif any(name.upper() in airline_upper for name in ALLOWED_AIRLINES.values()):
            filtered.append(airline)
    return filtered

def clean_sorted_unique(series):
    """Return a stable, case-insensitive sorted list of non-empty string values."""
    cleaned = (
        series.dropna()
        .astype("string")
        .str.strip()
    )
    cleaned = cleaned[cleaned.ne("")]
    return sorted(cleaned.unique().tolist(), key=str.casefold)

# Callback to update destination options when dataset origin changes (Chart 1)
@app.callback(
    Output("destination-filter-1", "options"),
    Output("destination-filter-1", "value"),
    Input("dataset-origin-1", "value")
)
def update_destinations_1(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback to update destination options when dataset origin changes (Chart 2)
@app.callback(
    Output("destination-filter-2", "options"),
    Output("destination-filter-2", "value"),
    Input("dataset-origin-2", "value")
)
def update_destinations_2(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback to update airline options (Chart 1)
@app.callback(
    Output("airline-filter-1", "options"),
    Output("airline-filter-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value")
)
def update_airline_options_1(selected_dataset_origin, selected_destination):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = datasets[selected_dataset_origin].copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Get unique airlines for this route
    available_airlines = filtered["Airline"].unique().tolist()

    # Filter to only allowed airlines
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback to update airline options (Chart 2)
@app.callback(
    Output("airline-filter-2", "options"),
    Output("airline-filter-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value")
)
def update_airline_options_2(selected_dataset_origin, selected_destination):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = datasets[selected_dataset_origin].copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Get unique airlines for this route
    available_airlines = filtered["Airline"].unique().tolist()

    # Filter to only allowed airlines
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback to update search date options (Chart 1)
@app.callback(
    Output("search-date-filter-1", "options"),
    Output("search-date-filter-1", "value"),
    Input("dataset-origin-1", "value")
)
def update_search_dates_1(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    search_dates = sorted(df["search_date"].dropna().unique())
    search_date_options = ["All"] + [pd.Timestamp(d).strftime("%Y-%m-%d") for d in search_dates]
    return search_date_options, "All"

# Callback to update search date options (Chart 2)
@app.callback(
    Output("search-date-filter-2", "options"),
    Output("search-date-filter-2", "value"),
    Input("dataset-origin-2", "value")
)
def update_search_dates_2(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    search_dates = sorted(df["search_date"].dropna().unique())
    search_date_options = ["All"] + [pd.Timestamp(d).strftime("%Y-%m-%d") for d in search_dates]
    return search_date_options, "All"

def style_cyberpunk_figure(fig, line_color=None, title=""):
    """Applies the dark modern aesthetic to Plotly figures."""
    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot background
        paper_bgcolor=PANEL_BG,        # Match panel background
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=50, r=30, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, tickprefix="$"),
    )
    if line_color:
        fig.update_traces(
            line=dict(color=line_color, width=3),
            marker=dict(size=8, color=line_color, line=dict(width=2, color=BG_COLOR)),
            mode="lines+markers"
        )
    return fig

# =====================================================================
# 6️⃣ AGGREGATION FUNCTION WITH CO2 DATA
# =====================================================================
def aggregate_price_data(filtered_df, agg_method='mean'):
    """
    Aggregate price data by date, preserving airline and CO2 information.
    For each date, calculate the mean/median price and average the CO2 values.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    agg_dict = {
        'Price': agg_method,
        'Airline': lambda x: ', '.join(x.dropna().unique()),  # Concatenate unique airlines
        'AvgCO2': 'mean'  # Average CO2 per hour
    }

    agg_df = filtered_df.groupby('Date').agg(agg_dict).reset_index()
    agg_df.columns = ['Date', 'Price', 'Airline', 'AvgCO2']

    return agg_df.sort_values('Date')

@app.callback(
    Output("price-chart-1", "figure"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value"),
    Input("airline-filter-1", "value"),
    Input("search-date-filter-1", "value")
)
def update_chart_1(selected_dataset_origin, selected_destination, selected_airline, selected_search_date):
    if selected_dataset_origin not in datasets:
        fig = px.scatter(title="NO SIGNAL: Dataset not loaded")
        return style_cyberpunk_figure(fig, line_color=NEON_CYAN, title="TRACKER ALPHA")

    filtered = datasets[selected_dataset_origin].copy()

    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]
    if selected_airline != "All":
        filtered = filtered[filtered["Airline"] == selected_airline]
    if selected_search_date != "All":
        filtered = filtered[filtered["search_date"] == pd.to_datetime(selected_search_date)]

    if filtered.empty:
        fig = px.scatter(title="NO SIGNAL: Data not found for Tracker Alpha")
        return style_cyberpunk_figure(fig, line_color=NEON_CYAN, title="TRACKER ALPHA")

    agg = aggregate_price_data(filtered, agg_method='mean')

    # Create figure with custom hover data
    hover_template = (
            "<b>Date:</b> %{x|%b %d, %Y}<br>" +
            "<b>Airline:</b> %{customdata[0]}<br>" +
            "<b>Price:</b> $%{y:.2f}<br>" +
            "<b>AVG CO2:</b> %{customdata[1]:.2f} kg/hr<br>" +
            "<extra></extra>"
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["Date"],
        y=agg["Price"],
        customdata=agg[["Airline", "AvgCO2"]],
        hovertemplate=hover_template,
        mode="lines+markers",
        name="Price Trend",
        line=dict(color=NEON_CYAN, width=3),
        marker=dict(size=8, color=NEON_CYAN, line=dict(width=2, color=BG_COLOR))
    ))

    title_text = f"TRACKER ALPHA: {selected_dataset_origin} → {selected_destination}"
    return style_cyberpunk_figure(fig, title=title_text)

@app.callback(
    Output("price-chart-2", "figure"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("airline-filter-2", "value"),
    Input("search-date-filter-2", "value")
)
def update_chart_2(selected_dataset_origin, selected_destination, selected_airline, selected_search_date):
    if selected_dataset_origin not in datasets:
        fig = px.scatter(title="NO SIGNAL: Dataset not loaded")
        return style_cyberpunk_figure(fig, line_color=NEON_PINK, title="TRACKER BETA")

    filtered = datasets[selected_dataset_origin].copy()

    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]
    if selected_airline != "All":
        filtered = filtered[filtered["Airline"] == selected_airline]
    if selected_search_date != "All":
        filtered = filtered[filtered["search_date"] == pd.to_datetime(selected_search_date)]

    if filtered.empty:
        fig = px.scatter(title="NO SIGNAL: Data not found for Tracker Beta")
        return style_cyberpunk_figure(fig, line_color=NEON_PINK, title="TRACKER BETA")

    agg = aggregate_price_data(filtered, agg_method='mean')

    # Create figure with custom hover data
    hover_template = (
            "<b>Date:</b> %{x|%b %d, %Y}<br>" +
            "<b>Airline:</b> %{customdata[0]}<br>" +
            "<b>Price:</b> $%{y:.2f}<br>" +
            "<b>AVG CO2:</b> %{customdata[1]:.2f} kg/hr<br>" +
            "<extra></extra>"
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["Date"],
        y=agg["Price"],
        customdata=agg[["Airline", "AvgCO2"]],
        hovertemplate=hover_template,
        mode="lines+markers",
        name="Price Trend",
        line=dict(color=NEON_PINK, width=3),
        marker=dict(size=8, color=NEON_PINK, line=dict(width=2, color=BG_COLOR))
    ))

    title_text = f"TRACKER BETA: {selected_dataset_origin} → {selected_destination}"
    return style_cyberpunk_figure(fig, title=title_text)

# =====================================================================
# 6️⃣ ROUTE ANALYTICS - Calculate AVG prices for all routes
# =====================================================================
def calculate_route_analytics(datasets):
    """Calculate average prices for all routes across all datasets"""
    route_prices = {}

    for origin_code, df in datasets.items():
        for destination in df['Destination'].unique():
            route_key = f"{origin_code}-{destination}"
            route_data = df[df['Destination'] == destination]
            avg_price = route_data['Price'].mean()
            route_prices[route_key] = avg_price

    return route_prices

# Callback for cheapest routes chart
@app.callback(
    Output("cheapest-routes-chart", "figure"),
    Input("destination-checklist-cheapest", "value")
)
def update_cheapest_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filter by selected destinations
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Sort and get 10 cheapest, reverse to show cheapest at the top
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1])[:10]
    sorted_routes.reverse()  # Reverse so cheapest is at the top
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=TRUE_PURPLE,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="10 CHEAPEST ROUTES",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Price ($)"),
        yaxis=dict(showgrid=False, title="Route"),
        height=400
    )

    return fig

# Callback for most expensive routes chart
@app.callback(
    Output("expensive-routes-chart", "figure"),
    Input("destination-checklist-expensive", "value")
)
def update_expensive_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filter by selected destinations
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Sort and get 10 most expensive, reverse to show most expensive at the top
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_routes.reverse()  # Reverse so most expensive is at the top
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=ELECTRIC_PURPLE,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="10 MOST EXPENSIVE ROUTES",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Price ($)"),
        yaxis=dict(showgrid=False, title="Route"),
        height=400
    )

    return fig

# Callback for origin comparison chart with destination filters
@app.callback(
    Output("origin-comparison-chart", "figure"),
    Input("destination-checklist", "value")
)
def update_origin_comparison(selected_destinations):
    origin_avg_prices = {}

    for origin_code, df in datasets.items():
        if selected_destinations:
            # Filter by selected destinations
            filtered_df = df[df['Destination'].isin(selected_destinations)]
        else:
            # If no destinations selected, use all
            filtered_df = df

        if not filtered_df.empty:
            avg_price = filtered_df['Price'].mean()
            origin_avg_prices[origin_code] = avg_price

    origins = list(origin_avg_prices.keys())
    prices = list(origin_avg_prices.values())

    fig = px.bar(
        x=prices,
        y=origins,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=CHART_CYAN,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="ORIGIN AIRPORT AVG PRICE COMPARISON",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Average Price ($)"),
        yaxis=dict(showgrid=False, title="Origin Airport"),
        height=400
    )

    return fig

# =====================================================================
# 5️⃣ MAIN EXECUTION
# =====================================================================
if __name__ == "__main__":

    # Load all 5 datasets into a dictionary
    print("Loading datasets...")
    datasets = {}
    for origin_code, file_path in DATASET_PATHS.items():
        try:
            df = load_data_from_file(file_path)
            datasets[origin_code] = df
            print(f"✓ Loaded {origin_code}: {len(df)} records")
        except Exception as e:
            print(f"✗ Error loading {origin_code} from {file_path}: {e}")

    if not datasets:
        print("⚠️  WARNING: No datasets loaded. Creating placeholder datasets...")
        datasets = {code: pd.DataFrame() for code in DATASET_PATHS.keys()}


    print(f"\n✓ Successfully loaded {len(datasets)} datasets\n")

    # Calculate and print route analytics
    print("="*60)
    print("ROUTE ANALYTICS - Average Prices by Route")
    print("="*60)

    route_prices = calculate_route_analytics(datasets)

    # Organize by origin
    origins = ['BER', 'BUD', 'PRG', 'VIE', 'WAW']

    for origin in origins:
        print(f"\n{origin} Routes:")
        origin_routes = {k: v for k, v in route_prices.items() if k.startswith(origin)}
        for route, price in sorted(origin_routes.items()):
            print(f"  {route}: ${price:.2f}")

    # Print variables for each specific route
    print("\n" + "="*60)
    print("INDIVIDUAL ROUTE VARIABLES")
    print("="*60)

    # Store in individual variables
    for route, price in sorted(route_prices.items()):
        var_name = route.replace('-', '_')
        print(f"{var_name} = ${price:.2f}")

    # Store in global scope
    globals().update({route.replace('-', '_'): price for route, price in route_prices.items()})

    print("\n" + "="*60)
    print(f"Total routes analyzed: {len(route_prices)}")
    print("="*60 + "\n")

    # ✅ Run app
# Remove or comment out:
if __name__ == '__main__':
    app.run(debug=True)