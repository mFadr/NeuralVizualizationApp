import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import io
import sys

# Cesty k CSV souborům mapované na kódy odletových letišť

from config import DATASET_PATHS
# =====================================================================
# 1️⃣ Funkce: Načtení CSV dat ze souboru
# =====================================================================
def load_data_from_file(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")

    # Vyčištění ceny
    df["price"] = df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)

    # Zajistí existenci očekávaných sloupců
    for col in ["departure_time", "duration", "Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col not in df.columns:
            df[col] = None

    # Převod departure_time
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

    # Převod na datetime
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")

    # Vyčištění názvu aerolinky
    df["airline"] = df["airline_details"].astype(str).str.strip()

    # Převod CO2 dat - ošetření různých formátů
    for col in ["Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    # Přejmenování sloupců
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
# 2️⃣ Konfigurace motivu (Cyberpunk styl)
# =====================================================================
# Barevná paleta
BG_COLOR = "#0b0c10"        # Hluboká černá
GWHITE = "#F8F8FF"             # Světle šedá pro text a mřížku
PANEL_BG = "#1f2833"        # Tmavě šedá pro panely
NEON_CYAN = "#66fcf1"       # Primární text/akcenty
NEON_BLUE = "#45a29e"       # Sekundární akcenty
NEON_PINK = "#ff007f"       # Kontrastní barva pro grafy
TEXT_MUTED = "#c5c6c7"      # Tlumený text
DROPDOWN_STYLE = {"color": "black", "marginBottom": "15px"} # Dropdowny potřebují tmavý text kvůli čitelnosti bez složitého CSS

# Nové barvy pro horizontální sloupcové grafy
TRUE_PURPLE = "#9D4EDD"      # 1. graf
ELECTRIC_PURPLE = "#7209B7"  # 2. graf
CHART_CYAN = "#00D9FF"       # 3. graf

# =====================================================================
# 3️⃣ Nastavení Dash aplikace (Layout + Callback)
# =====================================================================
from app_instance import app # sdílení jediné instance serveru
server = app.server

# Layout: použití Flexboxu místo pevných floatů a marginů
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

    # Hlavní kontejner
    html.Div([


        # Tlačítko zpět — vložit jako první potomka layout Divu
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

        # 🎛️ LEVÝ PANEL: Filtry
        html.Div([
            html.H3("SYSTEM PARAMETERS", style={"color": NEON_BLUE, "borderBottom": f"1px solid {NEON_BLUE}", "paddingBottom": "10px"}),

            # Filtry grafu 1
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

            # Filtry grafu 2
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

        # 📈 PRAVÝ PANEL: Grafy
        html.Div([

            # Kontejner grafu 1
            html.Div([
                dcc.Graph(id="price-chart-1")
            ], style={"borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_CYAN}80", "marginBottom": "30px"}),

            # Kontejner grafu 2
            html.Div([
                dcc.Graph(id="price-chart-2")
            ], style={"borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_PINK}80"})

        ], style={"width": "75%", "display": "flex", "flexDirection": "column"})

    ], style={"display": "flex", "gap": "30px"}),

    # 📊 SPODNÍ HORIZONTÁLNÍ SLOUPCOVÉ GRAFY (3 v jednom řádku)
    html.Div([
        # Graf 3: 10 nejlevnějších tras
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

        # Graf 4: 10 nejdražších tras
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

        # Graf 5: Porovnání odletových letišť s filtry
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
# 4️⃣ Callbacky a stylování grafů
# =====================================================================
# Definice mapování povolených aerolinek (IATA kód -> celý název)
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
        # Kontrola, zda aerolinka odpovídá některému kódu nebo názvu v ALLOWED_AIRLINES
        airline_upper = airline.upper()
        if airline in ALLOWED_AIRLINES or airline in ALLOWED_AIRLINES.values():
            filtered.append(airline)
        # Také kontrola, zda aerolinka obsahuje daný kód nebo název
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

# Callback pro aktualizaci možností destinace při změně odletového datasetu (graf 1)
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

# Callback pro aktualizaci možností destinace při změně odletového datasetu (graf 2)
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

# Callback pro aktualizaci možností aerolinek (graf 1)
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

    # Získání unikátních aerolinek pro tuto trasu
    available_airlines = filtered["Airline"].unique().tolist()

    # Filtrování pouze na povolené aerolinky
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback pro aktualizaci možností aerolinek (graf 2)
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

    # Získání unikátních aerolinek pro tuto trasu
    available_airlines = filtered["Airline"].unique().tolist()

    # Filtrování pouze na povolené aerolinky
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback pro aktualizaci možností data vyhledávání (graf 1)
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

# Callback pro aktualizaci možností data vyhledávání (graf 2)
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
        plot_bgcolor="rgba(0,0,0,0)",  # Transparentní pozadí grafu
        paper_bgcolor=PANEL_BG,        # Stejné pozadí jako panel
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
# 6️⃣ AGREGAČNÍ FUNKCE S CO2 DATY
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
        'Airline': lambda x: ', '.join(x.dropna().unique()),  # Spojení unikátních aerolinek
        'AvgCO2': 'mean'  # Průměrné CO2 za hodinu
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

    # Vytvoření grafu s vlastním hover obsahem
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

    # Vytvoření grafu s vlastním hover obsahem
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
# 6️⃣ ANALYTIKA TRAS - výpočet průměrných cen pro všechny trasy
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

# Callback pro graf nejlevnějších tras
@app.callback(
    Output("cheapest-routes-chart", "figure"),
    Input("destination-checklist-cheapest", "value")
)
def update_cheapest_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filtrování podle vybraných destinací
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Seřadí a vybere 10 nejlevnějších, pak obrátí pro zobrazení nejlevnějších nahoře
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1])[:10]
    sorted_routes.reverse()  # Obrácení pořadí, aby byly nejlevnější nahoře
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

# Callback pro graf nejdražších tras
@app.callback(
    Output("expensive-routes-chart", "figure"),
    Input("destination-checklist-expensive", "value")
)
def update_expensive_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filtrování podle vybraných destinací
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Seřadí a vybere 10 nejdražších, pak obrátí pro zobrazení nejdražších nahoře
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_routes.reverse()  # Obrácení pořadí, aby byly nejdražší nahoře
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

# Callback pro graf porovnání odletových letišť s filtry destinací
@app.callback(
    Output("origin-comparison-chart", "figure"),
    Input("destination-checklist", "value")
)
def update_origin_comparison(selected_destinations):
    origin_avg_prices = {}

    for origin_code, df in datasets.items():
        if selected_destinations:
            # Filtrování podle vybraných destinací
            filtered_df = df[df['Destination'].isin(selected_destinations)]
        else:
            # Pokud není vybrána žádná destinace, použije všechny
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
# 5️⃣ NAČTENÍ DATASETŮ — na úrovni modulu (spouští se při importu i přímém spuštění)
# =====================================================================
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

# =====================================================================
# 6️⃣ HLAVNÍ SPUŠTĚNÍ (jen pro lokální vývoj)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)