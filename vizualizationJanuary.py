import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from app_instance import app
from config import DATASET_PATHS
# =====================================================================
# 1️⃣ Funkce: Načítání dat CSV ze souboru
# =====================================================================
def load_data_from_file(file_path):
    df = pd.read_csv(
        file_path,
        sep=r"[\t;,]",
        engine="python",
        na_values=[""],
        keep_default_na=True,
        dtype=str
    )

    # Vyčištění ceny
    df["price"] = pd.to_numeric(df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")

    # Zajištění existence očekávaných sloupců
    for col in ["departure_time", "duration", "Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col not in df.columns:
            df[col] = None

    # Konverze departure_time
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

    # Konverze na datetime
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")

    # Vyčištění názvu aerolinky
    df["airline"] = df["airline_details"].astype(str).str.strip()

    # Sjednocený sloupec stavu letu (flown / flight canceled / ...).
    # Pokud sloupec ve zdroji chybí, předpokládá se, že všechny záznamy byly odlétnuty.
    if "flown_status" in df.columns:
        df["_status_col"] = df["flown_status"].astype(str).str.lower().str.strip()
    else:
        df["_status_col"] = "flown"

    # Zpracování dat CO2 - zpracování různých formátů
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
# 2️⃣ Konfigurace tématu (Cyberpunk styl)
# =====================================================================
# Barevná paleta
BG_COLOR = "#0b0c10"        # Hluboká černá
GWHITE = "#F8F8FF"             # Světle šedá pro text a mřížky
PANEL_BG = "#1f2833"        # Tmavě šedá pro panely
NEON_CYAN = "#66fcf1"       # Primární text/akcenty
NEON_BLUE = "#45a29e"       # Sekundární akcenty
NEON_PINK = "#ff007f"       # Kontrastní barva pro grafy
TEXT_MUTED = "#c5c6c7"      # Tlumený text
DROPDOWN_STYLE = {"color": "black", "marginBottom": "15px"} # Rozbalovací nabídky potřebují tmavý text pro čitelnost

# Nové barvy pro vodorovné sloupcové grafy
TRUE_PURPLE = "#9D4EDD"      # 1. graf
ELECTRIC_PURPLE = "#7209B7"  # 2. graf
CHART_CYAN = "#00D9FF"       # 3. graf

# Sdílená výška tak, aby filtrační panel a hlavní graf skončily na stejné spodní čáře
MAIN_PANEL_HEIGHT = "760px"

# =====================================================================
# 3️⃣ Rozložení
# =====================================================================

# ── Tlačítko zpět ──────────────────────────────────────────────────────
_back_btn = html.Div([
    html.A(
        "← BACK TO MAIN",
        href="/",
        style={
            "display":        "inline-block",
            "color":          NEON_CYAN,
            "border":         f"1px solid {NEON_BLUE}",
            "padding":        "6px 16px",
            "borderRadius":   "6px",
            "textDecoration": "none",
            "fontSize":       "11px",
            "letterSpacing":  "2px",
            "marginBottom":   "14px",
            "fontFamily":     "Courier New, monospace",
            "backgroundColor": PANEL_BG
        }
    ),
    html.P(
        "💡 Data not showing? The app may be warming up. Please press F5 to refresh.",
        style={
            "color": TEXT_MUTED,
            "fontSize": "10px",
            "marginTop": "8px",
            "marginBottom": "14px",
            "opacity": "0.7",
            "fontStyle": "italic"
        }
    )
])


layout = html.Div([_back_btn,
                   html.H2(
                       "✈️ NEURAL FLIGHT TRACKER v2.0 - VIZUALIZA CEN LETENEK Z LEDNA 2026",
                       style={
                           "textAlign": "center",
                           "textShadow": f"0 0 10px {NEON_CYAN}",
                           "letterSpacing": "3px",
                           "marginBottom": "30px"
                       }
                   ),

                   # Hlavní kontejner
                   html.Div([

                       # 🎛️ LEVÝ PANEL: Filtry
                       html.Div([
                           html.H3("SYSTÉMOVÉ PARAMETRY", style={"color": NEON_BLUE, "borderBottom": f"1px solid {NEON_BLUE}", "paddingBottom": "10px"}),

                           # Přepínač datového rozsahu (zrušené lety ANO/NE)
                           html.Div([
                               html.Label("Filtr zrušených letů", style={"color": TEXT_MUTED, "fontSize": "12px"}),
                               dcc.RadioItems(
                                   id="filter-status",
                                   options=[
                                       {"label": "  Zahrnout zrušené lety",    "value": "all"},
                                       {"label": "  Pouze uskutečněné lety",   "value": "flown"}
                                   ],
                                   value="all",
                                   labelStyle={"display": "block", "color": NEON_CYAN, "fontSize": "13px", "marginBottom": "4px"},
                                   inputStyle={"marginRight": "6px", "accentColor": NEON_CYAN},
                                   style={"marginTop": "6px", "marginBottom": "16px"}
                               )
                           ], style={"borderBottom": f"1px solid {NEON_BLUE}40", "paddingBottom": "12px", "marginBottom": "8px"}),

                           # Přepínač metody agregace
                           html.Div([
                               html.Label("Agregační metoda", style={"color": TEXT_MUTED, "fontSize": "12px"}),
                               dcc.RadioItems(
                                   id="agg-method",
                                   options=[
                                       {"label": "  Aritmetický průměr",   "value": "mean"},
                                       {"label": "  Medián", "value": "median"}
                                   ],
                                   value="mean",
                                   labelStyle={"display": "inline-block", "color": NEON_CYAN, "marginRight": "16px", "fontSize": "13px"},
                                   style={"marginTop": "6px", "marginBottom": "16px"}
                               )
                           ], style={"borderBottom": f"1px solid {NEON_BLUE}40", "paddingBottom": "12px", "marginBottom": "8px"}),

                           # Filtry Graf 1
                           html.Div([
                               html.H4("TRACKER ALFA", style={"color": NEON_CYAN, "marginTop": "20px"}),
                               html.Label("Počáteční letiště"),
                               dcc.Dropdown(
                                   id="dataset-origin-1",
                                   options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                                   value="PRG",
                                   style=DROPDOWN_STYLE
                               ),
                               html.Label("Destinace"),
                               dcc.Dropdown(id="destination-filter-1", value="AMS", style=DROPDOWN_STYLE),
                               html.Label("Aerolinie"),
                               dcc.Dropdown(id="airline-filter-1", value="All", style=DROPDOWN_STYLE),
                               html.Label("Výběr měsíců pro zobrazení"),
                               dcc.Dropdown(id="search-date-filter-1", value="All", style=DROPDOWN_STYLE)
                           ], style={"border": f"1px solid {NEON_CYAN}", "padding": "15px", "borderRadius": "10px", "marginBottom": "20px", "boxShadow": f"0 0 10px {NEON_CYAN}40"}),

                           # Filtry Graf 2
                           html.Div([
                               html.H4("TRACKER BETA", style={"color": NEON_PINK}),
                               html.Label("Počáteční letiště"),
                               dcc.Dropdown(
                                   id="dataset-origin-2",
                                   options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                                   value="PRG",
                                   style=DROPDOWN_STYLE
                               ),
                               html.Label("Destinace"),
                               dcc.Dropdown(id="destination-filter-2", value="FCO", style=DROPDOWN_STYLE),
                               html.Label("Aerolinie"),
                               dcc.Dropdown(id="airline-filter-2", value="All", style=DROPDOWN_STYLE),
                               html.Label("Výběr měsíců pro zobrazení"),
                               dcc.Dropdown(id="search-date-filter-2", value="All", style=DROPDOWN_STYLE)
                           ], style={"border": f"1px solid {NEON_PINK}", "padding": "15px", "borderRadius": "10px", "boxShadow": f"0 0 10px {NEON_PINK}40"})

                       ], style={
                           "width": "25%",
                           "backgroundColor": PANEL_BG,
                           "padding": "20px",
                           "borderRadius": "15px",
                           "boxShadow": f"0 0 20px {NEON_BLUE}60",
                           "height": MAIN_PANEL_HEIGHT,
                           "overflowY": "auto"
                       }),

                       # 📈 PRAVÝ PANEL: Grafy
                       html.Div([

                           # Sloučený graf - Oba trackery na stejném grafu
                           html.Div([
                               dcc.Graph(
                                   id="merged-price-chart",
                                   style={"height": "100%"},
                                   config={"responsive": True}
                               )
                           ], style={"height": MAIN_PANEL_HEIGHT, "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_CYAN}80", "marginBottom": "30px"}),



                       ], style={"width": "75%", "display": "flex", "flexDirection": "column"})

                   ], style={"display": "flex", "gap": "30px"}),

                   # 📊 SPODNÍ VODOROVNÉ SLOUPCOVÉ GRAFY (3 v jednom řádku)
                   html.Div([
                       # Graf 3: 10 Nejlevnějších tras
                       html.Div([
                           html.Div([
                               html.Label("Filtry destinací:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
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

                       # Graf 4: 10 Nejdražších tras
                       html.Div([
                           html.Div([
                               html.Label("Filtry destinací::", style={"color": NEON_CYAN, "marginBottom": "10px"}),
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

                       # Graf 5: Srovnání letiště původu s filtry
                       html.Div([
                           html.Div([
                               html.Label("Filtry destinací::", style={"color": NEON_CYAN, "marginBottom": "10px"}),
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
# 4️⃣ Callbacky & Stylizace grafů
# =====================================================================
# Definice mapování povolených leteckých společností (IATA kód na plný název)
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
        # Zkontroluj, zda se letecká společnost shoduje s jakýmkoli kódem nebo úplným názvem v ALLOWED_AIRLINES
        airline_upper = airline.upper()
        if airline in ALLOWED_AIRLINES or airline in ALLOWED_AIRLINES.values():
            filtered.append(airline)
        # Ověř také, zda letecká společnost obsahuje kód nebo název
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


def _apply_status_filter(df, status):
    """
    Filtr podle stavu letu (data scope switcher).
      status == "flown"  → pouze skutečně odlétnuté lety
      status == "all"    → všechny záznamy včetně zrušených letů
    """
    if status == "flown" and "_status_col" in df.columns:
        return df[df["_status_col"] == "flown"]
    return df

# Callback pro aktualizaci možností cíl při změně původního datasetu (Graf 1)
@app.callback(
    Output("destination-filter-1", "options"),
    Output("destination-filter-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("filter-status", "value")
)
def update_destinations_1(selected_dataset_origin, status):
    if selected_dataset_origin not in datasets:
        return [], None

    df = _apply_status_filter(datasets[selected_dataset_origin], status)
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback pro aktualizaci možností cíl při změně původního datasetu (Graf 2)
@app.callback(
    Output("destination-filter-2", "options"),
    Output("destination-filter-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("filter-status", "value")
)
def update_destinations_2(selected_dataset_origin, status):
    if selected_dataset_origin not in datasets:
        return [], None

    df = _apply_status_filter(datasets[selected_dataset_origin], status)
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback pro aktualizaci možností leteckých společností (Graf 1)
@app.callback(
    Output("airline-filter-1", "options"),
    Output("airline-filter-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value"),
    Input("filter-status", "value")
)
def update_airline_options_1(selected_dataset_origin, selected_destination, status):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = _apply_status_filter(datasets[selected_dataset_origin], status).copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Získat jedinečné letecké společnosti pro tuto trasu
    available_airlines = filtered["Airline"].unique().tolist()

    # Filtrovat pouze povolené letecké společnosti
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback pro aktualizaci možností leteckých společností (Graf 2)
@app.callback(
    Output("airline-filter-2", "options"),
    Output("airline-filter-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("filter-status", "value")
)
def update_airline_options_2(selected_dataset_origin, selected_destination, status):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = _apply_status_filter(datasets[selected_dataset_origin], status).copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Získat jedinečné letecké společnosti pro tuto trasu
    available_airlines = filtered["Airline"].unique().tolist()

    # Filtrovat pouze povolené letecké společnosti
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback pro aktualizaci možností data vyhledávání (Graf 1)
@app.callback(
    Output("search-date-filter-1", "options"),
    Output("search-date-filter-1", "value"),
    Input("dataset-origin-1", "value")
)
def update_search_dates_1(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]

    # Extrahuj měsíce z search_date
    df_temp = df.copy()
    df_temp['SearchMonth'] = df_temp['search_date'].dt.month
    df_temp['SearchMonthName'] = df_temp['search_date'].dt.strftime('%B')

    # Filtruj pro září(9), říjen(10), listopad(11), prosinec(12), leden(1)
    valid_months = [1, 9, 10, 11, 12]
    valid_data = df_temp[df_temp['SearchMonth'].isin(valid_months)][['SearchMonth', 'SearchMonthName']].drop_duplicates()

    # Seřadit měsíce správně
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    valid_data['SortOrder'] = valid_data['SearchMonth'].map(month_order)
    valid_data = valid_data.sort_values('SortOrder')

    month_options = ["All"] + valid_data['SearchMonthName'].unique().tolist()
    return month_options, "All"

# Callback pro aktualizaci možností data vyhledávání (Graf 2)
@app.callback(
    Output("search-date-filter-2", "options"),
    Output("search-date-filter-2", "value"),
    Input("dataset-origin-2", "value")
)
def update_search_dates_2(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]

    # Extrahuj měsíce z search_date
    df_temp = df.copy()
    df_temp['SearchMonth'] = df_temp['search_date'].dt.month
    df_temp['SearchMonthName'] = df_temp['search_date'].dt.strftime('%B')

    # Filtruj pro září(9), říjen(10), listopad(11), prosinec(12), leden(1)
    valid_months = [1, 9, 10, 11, 12]
    valid_data = df_temp[df_temp['SearchMonth'].isin(valid_months)][['SearchMonth', 'SearchMonthName']].drop_duplicates()

    # Seřadit měsíce správně
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    valid_data['SortOrder'] = valid_data['SearchMonth'].map(month_order)
    valid_data = valid_data.sort_values('SortOrder')

    month_options = ["All"] + valid_data['SearchMonthName'].unique().tolist()
    return month_options, "All"

def style_cyberpunk_figure(fig, line_color=None, title=""):
    """Applies the dark modern aesthetic to Plotly figures."""
    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",  # Průsvitné pozadí grafu
        paper_bgcolor=PANEL_BG,        # Shoduj se s pozadím panelu
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

def filter_by_month_name(df, month_name):
    """Filter dataframe by month name (Sep, Oct, Nov, Dec, Jan)"""
    if month_name == "All":
        valid_months = [1, 9, 10, 11, 12]
        return df[df['search_date'].dt.month.isin(valid_months)]
    else:
        return df[df['search_date'].dt.strftime('%B') == month_name]

# =====================================================================
# 6️⃣ FUNKCE AGREGACE S DATY CO2
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
        'Airline': lambda x: ', '.join(x.dropna().unique()),  # Zřetěz jedinečné aerolinky
        'AvgCO2': 'mean'  # Průměr CO2 za hodinu
    }

    agg_df = filtered_df.groupby('Date').agg(agg_dict).reset_index()
    agg_df.columns = ['Date', 'Price', 'Airline', 'AvgCO2']

    return agg_df.sort_values('Date')

@app.callback(
    Output("merged-price-chart", "figure"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value"),
    Input("airline-filter-1", "value"),
    Input("search-date-filter-1", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("airline-filter-2", "value"),
    Input("search-date-filter-2", "value"),
    Input("agg-method", "value"),
    Input("filter-status", "value")
)
def update_merged_chart(orig1, dest1, air1, month1, orig2, dest2, air2, month2, agg_method, status):
    """
    Display both TRACKER ALPHA and TRACKER BETA on the same chart for direct comparison
    """
    fig = go.Figure()

    hover_template = (
            "<b>Date:</b> %{x|%b %d, %Y}<br>" +
            "<b>Airline:</b> %{customdata[0]}<br>" +
            "<b>Price:</b> $%{y:.2f}<br>" +
            "<b>AVG CO2:</b> %{customdata[1]:.2f} kg/hr<br>" +
            "<extra></extra>"
    )

    def process(orig, dest, air, month_name):
        if orig not in datasets:
            return pd.DataFrame()

        df = _apply_status_filter(datasets[orig], status).copy()

        # Filtruj podle cíle
        if dest != "All":
            df = df[df["Destination"] == dest]

        # Filtruj podle letecké společnosti
        if air != "All":
            df = df[df["Airline"] == air]

        # Filtruj podle měsíce
        df = filter_by_month_name(df, month_name)

        if df.empty:
            return df

        # Agreguj podle data POUZE (jeden bod na datum přes všechny aerolinky)
        agg_dict = {
            'Price': agg_method,
            'Airline': lambda x: ', '.join(x.dropna().unique()),  # Zřetěz jedinečné aerolinky
            'AvgCO2': 'mean'  # Průměr CO2 za hodinu
        }
        agg_data = df.groupby('Date').agg(agg_dict).reset_index()

        return agg_data

    # Shání data pro oba trackery
    agg1 = process(orig1, dest1, air1, month1)
    agg2 = process(orig2, dest2, air2, month2)

    # Přidej TRACKER ALPHA
    if not agg1.empty:
        label = f"ALFA ({orig1} → {dest1})" if dest1 != "All" else f"ALPHA ({orig1})"
        fig.add_trace(go.Scatter(
            x=agg1["Datum"],
            y=agg1["Cena"],
            customdata=agg1[["Airline", "AvgCO2"]],
            hovertemplate=hover_template,
            mode="lines+markers",
            name=label,
            line=dict(color=NEON_CYAN, width=3),
            marker=dict(size=8, color=NEON_CYAN, line=dict(width=2, color=BG_COLOR))
        ))

    # Přidej TRACKER BETA
    if not agg2.empty:
        label = f"BETA ({orig2} → {dest2})" if dest2 != "All" else f"BETA ({orig2})"
        fig.add_trace(go.Scatter(
            x=agg2["Datum"],
            y=agg2["Cena"],
            customdata=agg2[["Airline", "AvgCO2"]],
            hovertemplate=hover_template,
            mode="lines+markers",
            name=label,
            line=dict(color=NEON_PINK, width=3),
            marker=dict(size=8, color=NEON_PINK, line=dict(width=2, color=BG_COLOR))
        ))

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    if agg1.empty and agg2.empty:
        title = f"Ztráta signalu: Upravte parametry pro načtení srovnání letů"
    else:
        title = f"SROVNÁVACÍ TABULKA CEN: Vývoj cen (ALFA vs. BETA)"

    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, title="Datum odletu spoje"),
        yaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, tickprefix="$", title=f"{metric} Cena ($)"),
        hovermode="x unified"
    )

    return fig

# =====================================================================
# 6️⃣ FUNKCE MĚSÍČNÍ AGREGACE
# =====================================================================
def aggregate_price_by_month(filtered_df, agg_method='mean'):
    """
    Aggregate price data by month (Sep, Oct, Nov, Dec, Jan).
    For each month, calculate the mean/median price.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    # Extrahuj měsíc ze sloupce Date
    filtered_df = filtered_df.copy()
    filtered_df['Month'] = filtered_df['Date'].dt.month
    filtered_df['MonthName'] = filtered_df['Date'].dt.strftime('%B')

    # Filtruj pro měsíce září(9), říjen(10), listopad(11), prosinec(12), leden(1)
    valid_months = [1, 9, 10, 11, 12]
    filtered_df = filtered_df[filtered_df['Month'].isin(valid_months)]

    if filtered_df.empty:
        return pd.DataFrame()

    # Agreguj podle měsíce
    agg_dict = {
        'Price': agg_method,
    }

    monthly_agg = filtered_df.groupby(['Month', 'MonthName']).agg(agg_dict).reset_index()
    monthly_agg.columns = ['Month', 'MonthName', 'Price']

    # Seřadit měsíce (leden nejdřív, pak září-prosinec)
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    monthly_agg['SortOrder'] = monthly_agg['Month'].map(month_order)
    monthly_agg = monthly_agg.sort_values('SortOrder').drop('SortOrder', axis=1)

    return monthly_agg

# =====================================================================
# 7️⃣ ANALÝZA TRAS - Výpočet průměrných cen pro všechny trasy
# =====================================================================

# Helper: Vygeneruj barevné přechody
def interpolate_color(color1, color2, factor):
    """Linear interpolation between two colors (hex format)"""
    c1_rgb = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
    c2_rgb = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
    result = tuple(int(c1_rgb[i] + (c2_rgb[i] - c1_rgb[i]) * factor) for i in range(3))
    return '#{:02x}{:02x}{:02x}'.format(*result)

def get_color_gradient(values, dark_color, light_color):
    """Create gradient colors based on values (0=dark, 1=light)"""
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    colors = []
    for val in values:
        factor = (val - min_val) / range_val
        color = interpolate_color(dark_color, light_color, factor)
        colors.append(color)
    return colors

def calculate_route_analytics(datasets, status="all", agg_method="mean"):
    """Calculate aggregated prices for all routes across all datasets.

    Parameters
    ----------
    datasets : dict
        Mapping of origin code -> DataFrame.
    status : str
        Data scope filter ("all" / "flown") - mirrors TRACKER ALPHA/BETA scope.
    agg_method : str
        Aggregation method ("mean" / "median") - mirrors TRACKER ALPHA/BETA.
    """
    route_prices = {}

    for origin_code, df in datasets.items():
        df = _apply_status_filter(df, status)
        for destination in df['Destination'].unique():
            route_key = f"{origin_code}-{destination}"
            route_data = df[df['Destination'] == destination]

            if route_data.empty or route_data['Price'].dropna().empty:
                continue

            if agg_method == "median":
                price = route_data['Price'].median()
            else:
                price = route_data['Price'].mean()

            route_prices[route_key] = price

    return route_prices


# Callback pro graf levnějších tras
@app.callback(
    Output("cheapest-routes-chart", "figure"),
    Input("destination-checklist-cheapest", "value"),
    Input("filter-status", "value"),
    Input("agg-method", "value")
)
def update_cheapest_routes(selected_destinations, status, agg_method):
    route_prices = calculate_route_analytics(datasets, status, agg_method)

    # Filtruj podle vybraných cílů
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Seřadit a získat 10 nejlevnějších, obrátit tak aby levnější byl na vrcholu
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1])[:10]
    sorted_routes.reverse()  # Obrátit tak aby levnější byl na vrcholu
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]


    # Bílá pro nejlevnější (vrchol), tmavá fialová pro dražší
    colors = get_color_gradient(prices, '#ffffff', '#3d1a4d') if prices else []

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    fig.update_layout(
        title=f"10 Nejlevnějších leteckých linek",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title=f"{metric} Cena ($)"),
        yaxis=dict(showgrid=False, title="Letecké linky"),
        height=400
    )

    return fig

# Callback pro graf nejdražších tras
@app.callback(
    Output("expensive-routes-chart", "figure"),
    Input("destination-checklist-expensive", "value"),
    Input("filter-status", "value"),
    Input("agg-method", "value")
)
def update_expensive_routes(selected_destinations, status, agg_method):
    route_prices = calculate_route_analytics(datasets, status, agg_method)

    # Filtruj podle vybraných cílů
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Seřadit a získat 10 nejdražších, obrátit tak aby nejdražší byl na vrcholu
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_routes.reverse()  # Obrátit tak aby nejdražší byl na vrcholu
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    # Tmavá purpurová pro nejdražší (vrchol), světlá purpurová pro levnější
    colors = get_color_gradient(prices, '#6b0080', '#e6b3ff') if prices else []

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    fig.update_layout(
        title=f"10 Nejdražších leteckých linek",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title=f"{metric} Cena ($)"),
        yaxis=dict(showgrid=False, title="Letecké linky"),
        height=400
    )

    return fig

# Callback pro graf srovnání letiště původu s filtry cílů
@app.callback(
    Output("origin-comparison-chart", "figure"),
    Input("destination-checklist", "value"),
    Input("filter-status", "value"),
    Input("agg-method", "value")
)
def update_origin_comparison(selected_destinations, status, agg_method):
    origin_avg_prices = {}

    for origin_code, df in datasets.items():
        df = _apply_status_filter(df, status)
        if selected_destinations:
            # Filtruj podle vybraných cílů
            filtered_df = df[df['Destination'].isin(selected_destinations)]
        else:
            # Pokud nejsou vybrány žádné cíle, použij všechny
            filtered_df = df

        if not filtered_df.empty and not filtered_df['Price'].dropna().empty:
            if agg_method == "median":
                price = filtered_df['Price'].median()
            else:
                price = filtered_df['Price'].mean()
            origin_avg_prices[origin_code] = price

    origins = list(origin_avg_prices.keys())
    prices = list(origin_avg_prices.values())

    # Tmavě modrá pro nejdražší, světlá modrá pro levnější
    colors = get_color_gradient(prices, '#003d4d', '#99e6f0') if prices else []

    fig = px.bar(
        x=prices,
        y=origins,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    fig.update_layout(
        title=f"Srovnání cenových úrovní výchozích letišť",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title=f"Cena ($)"),
        yaxis=dict(showgrid=False, title="Výchozí lety"),
        height=400
    )

    return fig

# =====================================================================
# 5️⃣ NAČÍTÁNÍ DATASETŮ — na úrovni modulu (běží při importu A při přímém spuštění)
# =====================================================================
print("Loading datasets (edit5)...")
datasets = {}
for origin_code, file_path in DATASET_PATHS.items():
    try:
        df = load_data_from_file(file_path)
        datasets[origin_code] = df
        print(f"✓ Loaded {origin_code}: {len(df)} records")
    except Exception as e:
        print(f"✗ Error loading {origin_code} from {file_path}: {e}")

if not datasets:
    print("WARNING: No datasets loaded — app will show empty state.")

print(f"\n✓ Successfully loaded {len(datasets)} datasets\n")

# =====================================================================
# 6️⃣ VSTUPNÍ BOD (pouze pro místní vývoj)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8057))
    app.run(host="0.0.0.0", port=port, debug=False)
