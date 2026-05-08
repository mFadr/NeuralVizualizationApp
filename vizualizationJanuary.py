import pandas as pd
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

# Sdílená výška tak, aby filtrační panel a hlavní graf skončily na stejné spodní čáře
MAIN_PANEL_HEIGHT = "760px"

# =====================================================================
# Klasifikace leteckých společností (Tradiční vs. Nízkonákladové)
# =====================================================================
TRADITIONAL_AIRLINES = [
    "Austrian Airlines",
    "KLM",
    "British Airways",
    "LOT Polish Airlines",
]

LOW_COST_AIRLINES = [
    "easyJet",
    "Wizz Air",
    "Wizz Air Malta",
    "Vueling Airlines",
    "Wizz Air U",
    "Smartwings",
    "Ryanair",
]

# Společný styl pro vícenásobná zaškrtávací pole leteckých společností
AIRLINE_CHECKLIST_STYLE = {
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "4px"
}
AIRLINE_CHECKLIST_LABEL_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "padding": "2px 4px",
    "borderRadius": "4px"
}
AIRLINE_CHECKLIST_INPUT_STYLE = {"marginRight": "6px", "accentColor": NEON_CYAN}
AIRLINE_COL_HEADER_STYLE = {
    "color": NEON_BLUE,
    "fontSize": "10px",
    "letterSpacing": "1px",
    "marginTop": "6px",
    "marginBottom": "4px",
    "display": "block"
}

# Společný styl pro vícenásobné zaškrtávací pole filtru měsíců
MONTH_CHECKLIST_STYLE = {
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "4px",
    "marginTop": "6px",
    "marginBottom": "12px"
}
MONTH_CHECKLIST_LABEL_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "padding": "2px 4px",
    "borderRadius": "4px"
}

# =====================================================================
# 3️⃣ Rozložení
# =====================================================================

# ── Tlačítko zpět ──────────────────────────────────────────────────────
_back_btn = html.Div([
    html.A(
        "← ZPĚT",
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
        "💡 Data se nezobrazují? Prosím stiskněte F5 pro obnovení stránky.",
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
                       "✈️ NEURAL FLIGHT TRACKER v2.0 - Vizualizace cen letenek z Ledna 2026",
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
                                       {"label": "  Zahrnout i zrušené lety",    "value": "all"},
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
                               html.Label("Výběr měsíců pro zobrazení"),
                               # Master přepínač "Vše" pro filtr měsíců
                               dcc.Checklist(
                                   id="month-select-all-1",
                                   options=[{"label": "  Vše", "value": "ALL"}],
                                   value=["ALL"],
                                   labelStyle={
                                       "color": NEON_CYAN,
                                       "fontSize": "12px",
                                       "marginTop": "6px",
                                       "marginBottom": "4px",
                                       "display": "block"
                                   },
                                   inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE
                               ),
                               # Vícenásobný výběr konkrétních měsíců (chronologicky)
                               dcc.Checklist(
                                   id="search-date-filter-1",
                                   options=[],
                                   value=[],
                                   labelStyle=MONTH_CHECKLIST_LABEL_STYLE,
                                   inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                                   style=MONTH_CHECKLIST_STYLE
                               ),
                               html.Label("Letecká společnost"),
                               # Master přepínač "Všechny letecké společnosti"
                               dcc.Checklist(
                                   id="airline-select-all-1",
                                   options=[{"label": "  Všechny letecké společnosti", "value": "ALL"}],
                                   value=["ALL"],
                                   labelStyle={
                                       "color": NEON_CYAN,
                                       "fontSize": "12px",
                                       "marginBottom": "6px",
                                       "display": "block"
                                   },
                                   inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE
                               ),
                               # Dvousloupcové uspořádání podle typu společnosti
                               html.Div([
                                   html.Div([
                                       html.Label("Tradiční společnosti", style=AIRLINE_COL_HEADER_STYLE),
                                       dcc.Checklist(
                                           id="airline-traditional-1",
                                           options=[],
                                           value=[],
                                           labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                                           inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                                           style=AIRLINE_CHECKLIST_STYLE
                                       )
                                   ], style={"flex": "1", "minWidth": "0"}),
                                   html.Div([
                                       html.Label("Nízkonákladové společnosti", style=AIRLINE_COL_HEADER_STYLE),
                                       dcc.Checklist(
                                           id="airline-lowcost-1",
                                           options=[],
                                           value=[],
                                           labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                                           inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                                           style=AIRLINE_CHECKLIST_STYLE
                                       )
                                   ], style={"flex": "1", "minWidth": "0"})
                               ], style={
                                   "display": "flex",
                                   "flexDirection": "row",
                                   "gap": "10px",
                                   "marginBottom": "8px"
                               })
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
                               html.Label("Výběr měsíců pro zobrazení"),
                               # Master přepínač "Vše" pro filtr měsíců
                               dcc.Checklist(
                                   id="month-select-all-2",
                                   options=[{"label": "  Vše", "value": "ALL"}],
                                   value=["ALL"],
                                   labelStyle={
                                       "color": NEON_PINK,
                                       "fontSize": "12px",
                                       "marginTop": "6px",
                                       "marginBottom": "4px",
                                       "display": "block"
                                   },
                                   inputStyle={"marginRight": "6px", "accentColor": NEON_PINK}
                               ),
                               # Vícenásobný výběr konkrétních měsíců (chronologicky)
                               dcc.Checklist(
                                   id="search-date-filter-2",
                                   options=[],
                                   value=[],
                                   labelStyle=MONTH_CHECKLIST_LABEL_STYLE,
                                   inputStyle={"marginRight": "6px", "accentColor": NEON_PINK},
                                   style=MONTH_CHECKLIST_STYLE
                               ),
                               html.Label("Letecká společnost"),
                               # Master přepínač "Všechny letecké společnosti"
                               dcc.Checklist(
                                   id="airline-select-all-2",
                                   options=[{"label": "  Všechny letecké společnosti", "value": "ALL"}],
                                   value=["ALL"],
                                   labelStyle={
                                       "color": NEON_PINK,
                                       "fontSize": "12px",
                                       "marginBottom": "6px",
                                       "display": "block"
                                   },
                                   inputStyle={"marginRight": "6px", "accentColor": NEON_PINK}
                               ),
                               # Dvousloupcové uspořádání podle typu společnosti
                               html.Div([
                                   html.Div([
                                       html.Label("Tradiční společnosti", style=AIRLINE_COL_HEADER_STYLE),
                                       dcc.Checklist(
                                           id="airline-traditional-2",
                                           options=[],
                                           value=[],
                                           labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                                           inputStyle={"marginRight": "6px", "accentColor": NEON_PINK},
                                           style=AIRLINE_CHECKLIST_STYLE
                                       )
                                   ], style={"flex": "1", "minWidth": "0"}),
                                   html.Div([
                                       html.Label("Nízkonákladové společnosti", style=AIRLINE_COL_HEADER_STYLE),
                                       dcc.Checklist(
                                           id="airline-lowcost-2",
                                           options=[],
                                           value=[],
                                           labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                                           inputStyle={"marginRight": "6px", "accentColor": NEON_PINK},
                                           style=AIRLINE_CHECKLIST_STYLE
                                       )
                                   ], style={"flex": "1", "minWidth": "0"})
                               ], style={
                                   "display": "flex",
                                   "flexDirection": "row",
                                   "gap": "10px",
                                   "marginBottom": "8px"
                               })
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

# =====================================================================
# Pomocné funkce pro klasifikaci a porovnávání aerolinek
# =====================================================================
def _airline_matches(value, target_name):
    """Posoudí, zda hodnota ze sloupce Airline odpovídá cílovému názvu společnosti.

    Porovnává se bez ohledu na velikost písmen a tolerují se varianty zápisu
    (např. EasyJet vs. easyJet, plný název obsahující IATA kód apod.).
    """
    if value is None:
        return False
    val = str(value).strip().lower()
    if not val:
        return False
    name = str(target_name).strip().lower()
    return val == name or name in val or val in name


def split_airlines_by_type(available_airlines):
    """Rozdělí seznam dostupných aerolinek na tradiční a nízkonákladové.

    Vrací dvojici seznamů (traditional, low_cost), v níž jsou položky
    reprezentované původním zápisem ze zdrojových dat (zachovává se pořadí
    dle definovaných seznamů). Každá hodnota se přiřadí maximálně jednou.
    """
    traditional, low_cost = [], []
    used = set()

    for canonical in TRADITIONAL_AIRLINES:
        for raw in available_airlines:
            if raw in used:
                continue
            if _airline_matches(raw, canonical):
                traditional.append(raw)
                used.add(raw)

    for canonical in LOW_COST_AIRLINES:
        for raw in available_airlines:
            if raw in used:
                continue
            if _airline_matches(raw, canonical):
                low_cost.append(raw)
                used.add(raw)

    return traditional, low_cost


# Callback pro aktualizaci možností leteckých společností (Graf 1)
@app.callback(
    Output("airline-traditional-1", "options"),
    Output("airline-traditional-1", "value"),
    Output("airline-lowcost-1", "options"),
    Output("airline-lowcost-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value"),
    Input("filter-status", "value"),
    Input("airline-select-all-1", "value")
)
def update_airline_options_1(selected_dataset_origin, selected_destination, status, select_all):
    if selected_dataset_origin not in datasets:
        return [], [], [], []

    filtered = _apply_status_filter(datasets[selected_dataset_origin], status).copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Získat jedinečné letecké společnosti pro tuto trasu
    available_airlines = filtered["Airline"].unique().tolist()

    # Filtrovat pouze povolené letecké společnosti (zachová původní logiku)
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    # Rozdělit do dvou sloupců podle typu společnosti
    traditional, low_cost = split_airlines_by_type(allowed_route_airlines)

    trad_options = [{"label": f"  {name}", "value": name} for name in traditional]
    low_options  = [{"label": f"  {name}", "value": name} for name in low_cost]

    # Pokud je aktivní volba "Všechny letecké společnosti", předvyber vše dostupné.
    if select_all and "ALL" in select_all:
        trad_value = list(traditional)
        low_value  = list(low_cost)
    else:
        trad_value = []
        low_value  = []

    return trad_options, trad_value, low_options, low_value


# Callback pro aktualizaci možností leteckých společností (Graf 2)
@app.callback(
    Output("airline-traditional-2", "options"),
    Output("airline-traditional-2", "value"),
    Output("airline-lowcost-2", "options"),
    Output("airline-lowcost-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("filter-status", "value"),
    Input("airline-select-all-2", "value")
)
def update_airline_options_2(selected_dataset_origin, selected_destination, status, select_all):
    if selected_dataset_origin not in datasets:
        return [], [], [], []

    filtered = _apply_status_filter(datasets[selected_dataset_origin], status).copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    available_airlines = filtered["Airline"].unique().tolist()
    allowed_route_airlines = filter_allowed_airlines(available_airlines)
    traditional, low_cost = split_airlines_by_type(allowed_route_airlines)

    trad_options = [{"label": f"  {name}", "value": name} for name in traditional]
    low_options  = [{"label": f"  {name}", "value": name} for name in low_cost]

    if select_all and "ALL" in select_all:
        trad_value = list(traditional)
        low_value  = list(low_cost)
    else:
        trad_value = []
        low_value  = []

    return trad_options, trad_value, low_options, low_value

# =====================================================================
# Lokalizace nabídky měsíců do češtiny (chronologické řazení)
# =====================================================================
# Mapování (rok, měsíc) → český popisek používaný v rozbalovací nabídce.
# Pořadí klíčů odpovídá očekávanému chronologickému zobrazení.
MONTH_LABELS_CZ = {
    (2025, 9):  "Září 2025",
    (2025, 10): "Říjen 2025",
    (2025, 11): "Listopad 2025",
    (2025, 12): "Prosinec 2025",
    (2026, 1):  "Leden 2026",
}


def _build_month_options(df):
    """Vytvoří seznam možností pro filtr měsíců s českými popisky.

    Z dostupných dat se vyberou pouze ty kombinace (rok, měsíc), které jsou
    obsaženy ve slovníku MONTH_LABELS_CZ. Výsledný seznam je vždy seřazen
    chronologicky podle pořadí klíčů ve slovníku. Vrací dvojici (options, all_values),
    kde all_values je seznam všech dostupných popisků (pro předvolbu master přepínače).
    """
    if df.empty or "search_date" not in df.columns:
        return [], []

    available = (
        df.dropna(subset=["search_date"])
        .assign(
            _year=lambda d: d["search_date"].dt.year.astype("Int64"),
            _month=lambda d: d["search_date"].dt.month.astype("Int64"),
        )[["_year", "_month"]]
        .drop_duplicates()
    )
    available_pairs = {
        (int(y), int(m))
        for y, m in zip(available["_year"], available["_month"])
        if pd.notna(y) and pd.notna(m)
    }

    options = []
    all_values = []
    for key in MONTH_LABELS_CZ:
        if key in available_pairs:
            label = MONTH_LABELS_CZ[key]
            options.append({"label": f"  {label}", "value": label})
            all_values.append(label)
    return options, all_values


# Callback pro aktualizaci možností filtru měsíců (Graf 1)
@app.callback(
    Output("search-date-filter-1", "options"),
    Output("search-date-filter-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("month-select-all-1", "value")
)
def update_search_dates_1(selected_dataset_origin, select_all):
    if selected_dataset_origin not in datasets:
        return [], []

    options, all_values = _build_month_options(datasets[selected_dataset_origin])
    # Pokud je aktivní volba "Vše", předvyber všechny dostupné měsíce.
    if select_all and "ALL" in select_all:
        return options, all_values
    return options, []


# Callback pro aktualizaci možností filtru měsíců (Graf 2)
@app.callback(
    Output("search-date-filter-2", "options"),
    Output("search-date-filter-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("month-select-all-2", "value")
)
def update_search_dates_2(selected_dataset_origin, select_all):
    if selected_dataset_origin not in datasets:
        return [], []

    options, all_values = _build_month_options(datasets[selected_dataset_origin])
    if select_all and "ALL" in select_all:
        return options, all_values
    return options, []

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

def filter_by_month_name(df, month_names):
    """Filtr dat podle vybraných českých popisků měsíců (např. "Září 2025").

    Parametr month_names je seznam vybraných popisků z dcc.Checklist.
    Pokud je seznam prázdný, ponechá se chování ekvivalentní původnímu "All",
    tedy filtrace na všechny dvojice (rok, měsíc) definované v MONTH_LABELS_CZ.
    """
    if df.empty or "search_date" not in df.columns:
        return df

    # Zpětná kompatibilita: pokud přijde řetězec namísto seznamu, převede se
    if month_names is None:
        month_names = []
    elif isinstance(month_names, str):
        month_names = [] if month_names == "All" else [month_names]

    valid_pairs = list(MONTH_LABELS_CZ.keys())

    # Prázdný výběr ekvivalentně původnímu "All": ponechat všechna platná období
    if not month_names:
        years = df["search_date"].dt.year
        months = df["search_date"].dt.month
        mask = pd.Series(False, index=df.index)
        for y, m in valid_pairs:
            mask = mask | ((years == y) & (months == m))
        return df[mask]

    # Konkrétní výběr: sestavit masku ze všech zvolených dvojic (rok, měsíc)
    label_to_pair = {v: k for k, v in MONTH_LABELS_CZ.items()}
    targets = [label_to_pair[name] for name in month_names if name in label_to_pair]
    if not targets:
        return df.iloc[0:0]

    years = df["search_date"].dt.year
    months = df["search_date"].dt.month
    mask = pd.Series(False, index=df.index)
    for y, m in targets:
        mask = mask | ((years == y) & (months == m))
    return df[mask]

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
    Input("airline-traditional-1", "value"),
    Input("airline-lowcost-1", "value"),
    Input("search-date-filter-1", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("airline-traditional-2", "value"),
    Input("airline-lowcost-2", "value"),
    Input("search-date-filter-2", "value"),
    Input("agg-method", "value"),
    Input("filter-status", "value")
)
def update_merged_chart(orig1, dest1, air1_trad, air1_low, month1,
                        orig2, dest2, air2_trad, air2_low, month2,
                        agg_method, status):
    """
    Display both TRACKER ALPHA and TRACKER BETA on the same chart for direct comparison
    """
    # Spojení vybraných tradičních a nízkonákladových společností
    air1 = list(air1_trad or []) + list(air1_low or [])
    air2 = list(air2_trad or []) + list(air2_low or [])

    fig = go.Figure()

    hover_template = (
            "<b>Date:</b> %{x|%b %d, %Y}<br>" +
            "<b>Airline:</b> %{customdata[0]}<br>" +
            "<b>Price:</b> $%{y:.2f}<br>" +
            "<b>AVG CO2:</b> %{customdata[1]:.2f} kg/hr<br>" +
            "<extra></extra>"
    )

    def process(orig, dest, air, months_selected):
        if orig not in datasets:
            return pd.DataFrame()

        df = _apply_status_filter(datasets[orig], status).copy()

        # Filtruj podle cíle
        if dest != "All":
            df = df[df["Destination"] == dest]

        # Filtruj podle leteckých společností (vícenásobný výběr).
        # Pokud nebyla zvolena žádná společnost, ponechá se kompletní dataset
        # v duchu původní volby "All".
        if air:
            df = df[df["Airline"].isin(air)]

        # Filtruj podle vybraných měsíců (seznam českých popisků)
        df = filter_by_month_name(df, months_selected)

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
            x=agg1["Date"],
            y=agg1["Price"],
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
            x=agg2["Date"],
            y=agg2["Price"],
            customdata=agg2[["Airline", "AvgCO2"]],
            hovertemplate=hover_template,
            mode="lines+markers",
            name=label,
            line=dict(color=NEON_PINK, width=3),
            marker=dict(size=8, color=NEON_PINK, line=dict(width=2, color=BG_COLOR))
        ))

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    if agg1.empty and agg2.empty:
        title = f"NO SIGNAL: Adjust parameters to load {metric} Price Comparison"
    else:
        title = f"PRICE COMPARISON MATRIX: {metric} Price Trends (ALPHA vs BETA)"

    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, title="Departure Date"),
        yaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, tickprefix="$", title=f"{metric} Price ($)"),
        hovermode="x unified"
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