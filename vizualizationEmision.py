import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import sys

# =====================================================================
# 1. Konfigurace
# =====================================================================
from config import DATASET_PATHS

# Rozsah dat na ose X — pevně nastavený na leden 2026
DATE_START = pd.Timestamp("2026-01-01")
DATE_END   = pd.Timestamp("2026-01-31")

# =====================================================================
# 2. Cyberpunk téma
# =====================================================================
BG_COLOR       = "#0b0c10"
PANEL_BG       = "#1f2833"
NEON_CYAN      = "#66fcf1"
NEON_BLUE      = "#45a29e"
NEON_PINK      = "#ff007f"
NEON_YELLOW    = "#f5c518"
NEON_GREEN     = "#39ff14"
NEON_ORANGE    = "#ff6600"
TEXT_MUTED     = "#c5c6c7"
GRID_COLOR     = "#1e2a2a"
DROPDOWN_STYLE = {"color": "black"}

# Paleta barev pro křivky (aerolinky/trasy se přes ně cyklicky střídají)
TRACE_COLORS = [
    NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_GREEN, NEON_ORANGE,
    "#a855f7", "#00d4ff", "#ff3366", "#ffcc00", "#00ff99"
]

LABEL_STYLE = {
    "color": NEON_BLUE,
    "fontSize": "10px",
    "letterSpacing": "1px",
    "marginBottom": "4px",
    "display": "block"
}
FILTER_CELL = {
    "display": "inline-block",
    "verticalAlign": "top",
    "marginRight": "18px"
}

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

# Společné styly pro vícenásobná zaškrtávací pole leteckých společností
AIRLINE_CHECKLIST_STYLE = {
    "color": TEXT_MUTED,
    "fontSize": "11px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "3px",
    "marginTop": "4px"
}
AIRLINE_CHECKLIST_LABEL_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "color": TEXT_MUTED,
    "fontSize": "11px",
    "padding": "1px 4px",
    "borderRadius": "4px",
    "lineHeight": "1.2"
}
AIRLINE_CHECKLIST_INPUT_STYLE = {"marginRight": "6px", "accentColor": NEON_CYAN}
AIRLINE_GROUP_HEADER_STYLE = {
    "color": NEON_BLUE,
    "fontSize": "10px",
    "letterSpacing": "1px",
    "marginTop": "0px",
    "marginBottom": "4px",
    "display": "block"
}

# =====================================================================
# 3. Načítání dat
# =====================================================================
def load_data(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(".", "_", regex=False)

    # Normalizace klíčových názvů sloupců
    rename_map = {}
    for col in df.columns:
        if col in ("airline_details", "airline"):
            rename_map[col] = "_airline"
        elif col in ("destination", "dest"):
            rename_map[col] = "destination"
        elif "est__co2" in col or "est._co2" in col or col == "est__co2_(kg)":
            rename_map[col] = "est_co2_kg"
        elif "avg_co2" in col:
            rename_map[col] = "avg_co2_hr"
        elif "est__fuel" in col or "est._fuel" in col:
            rename_map[col] = "est_fuel_kg"
    df.rename(columns=rename_map, inplace=True)

    # Ošetří také přesné názvy sloupců ze vzorové hlavičky
    col_map = {}
    for col in df.columns:
        if "est" in col and "co2" in col and "kg" in col:
            col_map[col] = "est_co2_kg"
        elif "avg" in col and "co2" in col:
            col_map[col] = "avg_co2_hr"
        elif "est" in col and "fuel" in col:
            col_map[col] = "est_fuel_kg"
    for old, new in col_map.items():
        if old not in df.columns or new in df.columns:
            continue
        df.rename(columns={old: new}, inplace=True)

    # Převod datumů
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")
    df["flight_date"]  = pd.to_datetime(df["flight_date"],  errors="coerce")
    df = df.dropna(subset=["search_date", "flight_date"])

    # Filtr pouze na data letů v lednu 2026
    df = df[(df["flight_date"] >= DATE_START) & (df["flight_date"] <= DATE_END)]

    # Převod ceny
    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors="coerce"
    )

    # Převod CO2 sloupců — nahrazuje text 'Flight Canceled' hodnotou NaN pro číselné operace
    for col in ["est_co2_kg", "avg_co2_hr", "est_fuel_kg", "emissions_per_seat_(avg)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    # Normalizace názvu sloupce emissions_per_seat (u oddělovače středníkem se může lišit mezera)
    for col in list(df.columns):
        if "emission" in col and "seat" in col:
            df.rename(columns={col: "emissions_per_seat"}, inplace=True)
            break
    if "emissions_per_seat" not in df.columns:
        df["emissions_per_seat"] = np.nan

    # Zajistí existenci pomocných sloupců
    if "_airline" not in df.columns:
        df["_airline"] = "Unknown"
    if "aircraft" not in df.columns:
        df["aircraft"] = "Unknown"
    if "destination" not in df.columns:
        df["destination"] = "Unknown"

    df["_airline"]    = df["_airline"].astype(str).str.strip()
    df["aircraft"]    = df["aircraft"].astype(str).str.strip()
    df["destination"] = df["destination"].astype(str).str.strip().str.upper()

    return df


print("Načítám datasety...")
datasets = {}
for code, path in DATASET_PATHS.items():
    try:
        datasets[code] = load_data(path)
        n = len(datasets[code])
        print(f"✓ {code}: {n} záznamů v lednu 2026")
    except Exception as e:
        print(f"✗ {code}: {e}")

if not datasets:
    print("⚠️  VAROVÁNÍ: Žádné datasety nebyly načteny. Vytvářím zástupné datasety...")
    datasets = {code: pd.DataFrame() for code in DATASET_PATHS.keys()}

origins = list(datasets.keys())

# =====================================================================
# 4. Pomocné funkce
# =====================================================================
def get_destinations(origin):
    if origin not in datasets:
        return [{"label": "Vše", "value": "All"}]
    vals = sorted(datasets[origin]["destination"].dropna().unique())
    vals = [v for v in vals if v and v != "nan"]
    return [{"label": "Vše", "value": "All"}] + [{"label": v, "value": v} for v in vals]


def get_airlines_old_unused(origin, dest):
    """Stará funkce zachovaná pouze pro případnou zpětnou kompatibilitu.
    V aktuálním kódu se nevolá; nahrazena get_available_airlines + split_airlines_by_type.
    """
    if origin not in datasets:
        return [{"label": "Vše", "value": "All"}]
    df = datasets[origin].copy()
    if dest != "All":
        df = df[df["destination"] == dest]
    vals = sorted(v for v in df["_airline"].dropna().unique() if v and v != "nan")
    return [{"label": "Vše", "value": "All"}] + [{"label": v, "value": v} for v in vals]


# =====================================================================
# Pomocné funkce pro klasifikaci aerolinek (Tradiční vs. Nízkonákladové)
# =====================================================================
def _airline_matches(value, target_name):
    """Posoudí, zda hodnota ze sloupce _airline odpovídá cílovému názvu společnosti.

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
    podle definovaných seznamů). Každá hodnota se přiřadí maximálně jednou.
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


def get_available_airlines(origin, dest):
    """Vrátí seznam unikátních aerolinek dostupných pro danou trasu.

    Vrací holý seznam názvů použitelný pro split_airlines_by_type
    (na rozdíl od formátu options pro dropdown / checklist).
    """
    if origin not in datasets:
        return []
    df = datasets[origin].copy()
    if dest != "All":
        df = df[df["destination"] == dest]
    return sorted(v for v in df["_airline"].dropna().unique() if v and v != "nan")


# =====================================================================
# 5. Rozložení
# =====================================================================
from app_instance import app  # sdílení jediné instance serveru
server = app.server

DIVIDER = html.Span(style={
    "display": "inline-block",
    "width": "1px", "height": "44px",
    "backgroundColor": NEON_BLUE,
    "verticalAlign": "middle",
    "opacity": "0.35",
    "marginRight": "18px"
})

layout = html.Div([

    # ── Překryv skenovacích čar (čistě dekorativní CSS) ────────────────
    html.Div(style={
        "position": "fixed", "top": 0, "left": 0,
        "width": "100%", "height": "100%",
        "backgroundImage": "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        "pointerEvents": "none", "zIndex": 9999
    }),

    # ── Titulek ────────────────────────────────────────────────────────
    html.Div([
        html.H2("Porovnání emisí leteckých společností", style={
            "display": "inline-block",
            "color": NEON_CYAN,
            "textShadow": f"0 0 20px {NEON_CYAN}, 0 0 40px {NEON_CYAN}40",
            "letterSpacing": "5px",
            "fontSize": "18px",
            "margin": 0,
            "fontFamily": "'Courier New', monospace",
            "verticalAlign": "middle"
        }),

        html.Div("Sledování uhlíkové stopy u jednotlivých typů letadel  //  Leden 2026", style={
            "color": NEON_BLUE,
            "fontSize": "10px",
            "letterSpacing": "4px",
            "marginTop": "4px",
            "fontFamily": "'Courier New', monospace"
        }),
        html.A(
            "← Zpět",
            href="/",
            style={
                "position": "absolute",
                "top": "0",
                "left": "0",
                "display": "inline-block",
                "color": "#66fcf1",
                "border": "1px solid #45a29e",
                "padding": "6px 16px",
                "borderRadius": "6px",
                "textDecoration": "none",
                "fontSize": "11px",
                "letterSpacing": "2px",
                "fontFamily": "Courier New, monospace",
                "backgroundColor": "#1f2833"
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
    ], style={"textAlign": "center", "marginBottom": "20px", "position": "relative"}),

    # ── Graf ───────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(
            id="em-chart",
            style={"height": "72vh", "width": "100%"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={
        "borderRadius": "14px",
        "overflow": "hidden",
        "boxShadow": f"0 0 30px {NEON_CYAN}30, 0 0 60px {NEON_CYAN}10",
        "border": f"1px solid {NEON_CYAN}20"
    }),

    # ── Lišta filtrů ───────────────────────────────────────────────────
    html.Div([

        # Počáteční letiště
        html.Div([
            html.Label("Výchozí letiště", style=LABEL_STYLE),
            dcc.Dropdown(
                id="em-origin",
                options=[{"label": o, "value": o} for o in origins],
                value=origins[0],
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "100px"}
            )
        ], style=FILTER_CELL),

        # Cílové letiště
        html.Div([
            html.Label("Destinace", style=LABEL_STYLE),
            dcc.Dropdown(
                id="em-dest",
                value="All",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "120px"}
            )
        ], style=FILTER_CELL),

        # Aerolinka — vícenásobný výběr s rozdělením na tradiční a nízkonákladové
        html.Div([
            html.Label("Letecká společnost", style=LABEL_STYLE),
            # Master přepínač "Všechny letecké společnosti"
            dcc.Checklist(
                id="airline-select-all",
                options=[{"label": "  Všechny letecké společnosti", "value": "ALL"}],
                value=["ALL"],
                labelStyle={
                    "color": NEON_CYAN,
                    "fontSize": "11px",
                    "marginBottom": "6px",
                    "display": "block",
                    "lineHeight": "1.2"
                },
                inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE
            ),
            # Dvousloupcové uspořádání: Tradiční vlevo, Nízkonákladové vpravo
            html.Div([
                html.Div([
                    html.Label("Tradiční", style=AIRLINE_GROUP_HEADER_STYLE),
                    dcc.Checklist(
                        id="airline-traditional",
                        options=[],
                        value=[],
                        labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                        inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                        style=AIRLINE_CHECKLIST_STYLE
                    )
                ], style={"flex": "1", "minWidth": "150px", "marginRight": "10px"}),
                html.Div([
                    html.Label("Nízkonákladové", style=AIRLINE_GROUP_HEADER_STYLE),
                    dcc.Checklist(
                        id="airline-lowcost",
                        options=[],
                        value=[],
                        labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                        inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                        style=AIRLINE_CHECKLIST_STYLE
                    )
                ], style={"flex": "1", "minWidth": "150px"})
            ], style={"display": "flex", "flexDirection": "row", "gap": "10px"})
        ], style={**FILTER_CELL, "minWidth": "320px"}),

        DIVIDER,

        # Režim vizualizace
        html.Div([
            html.Label("Výběr způsobu vizualizace emisí", style=LABEL_STYLE),
            dcc.RadioItems(
                id="em-mode",
                options=[
                    {"label": "  Průměrné CO₂  (kg/hod)",        "value": "avg"},
                    {"label": "  Odhadované CO₂  (kg/let)",   "value": "est"},
                    {"label": "  Emise / Sedadlo  (kg/hod)", "value": "per_seat"}
                ],
                value="avg",
                labelStyle={
                    "display": "inline-block",
                    "color": TEXT_MUTED,
                    "marginRight": "16px",
                    "fontSize": "13px"
                }
            )
        ], style=FILTER_CELL),

        DIVIDER,

        # Seskupení podle
        html.Div([
            html.Label("Filtrovat data podle", style=LABEL_STYLE),
            dcc.RadioItems(
                id="em-groupby",
                options=[
                    {"label": "  Letecká společnost",  "value": "airline"},
                    {"label": "  Typ letadla", "value": "aircraft"}
                ],
                value="airline",
                labelStyle={
                    "display": "inline-block",
                    "color": TEXT_MUTED,
                    "marginRight": "12px",
                    "fontSize": "13px"
                }
            )
        ], style=FILTER_CELL),

    ], style={
        "backgroundColor": PANEL_BG,
        "padding": "12px 22px",
        "borderRadius": "12px",
        "marginBottom": "16px",
        "boxShadow": f"0 0 18px {NEON_BLUE}50, inset 0 0 30px rgba(0,0,0,0.3)",
        "border": f"1px solid {NEON_BLUE}30",
        "display": "flex",
        "alignItems": "center",
        "flexWrap": "wrap"
    }),

    # ── Řádek statistik ────────────────────────────────────────────────
    html.Div(id="em-stats", style={
        "backgroundColor": PANEL_BG,
        "padding": "8px 20px",
        "borderRadius": "10px",
        "marginBottom": "14px",
        "fontSize": "11px",
        "color": TEXT_MUTED,
        "border": f"1px solid {NEON_BLUE}20",
        "fontFamily": "'Courier New', monospace",
        "overflowX": "auto",
        "whiteSpace": "nowrap"
    }),


], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "22px 26px",
    "fontFamily": "'Courier New', monospace",
    "boxSizing": "border-box"
})

# =====================================================================
# 6. Callbacky
# =====================================================================
@app.callback(
    Output("em-dest",    "options"),
    Output("em-dest",    "value"),
    Input("em-origin",   "value")
)
def update_dest(origin):
    opts = get_destinations(origin)
    default = opts[1]["value"] if len(opts) > 1 else "All"
    return opts, default


@app.callback(
    Output("airline-traditional", "options"),
    Output("airline-traditional", "value"),
    Output("airline-lowcost", "options"),
    Output("airline-lowcost", "value"),
    Input("em-origin",   "value"),
    Input("em-dest",     "value"),
    Input("airline-select-all", "value")
)
def update_airline(origin, dest, select_all):
    available = get_available_airlines(origin, dest)
    traditional, low_cost = split_airlines_by_type(available)

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


@app.callback(
    Output("em-chart",  "figure"),
    Output("em-stats",  "children"),
    Input("em-origin",  "value"),
    Input("em-dest",    "value"),
    Input("airline-traditional", "value"),
    Input("airline-lowcost",     "value"),
    Input("em-mode",    "value"),
    Input("em-groupby", "value")
)
def update_chart(origin, dest, air_trad, air_low, mode, groupby):

    if origin not in datasets:
        return _empty_fig("Žádný signál — dataset není načten"), "—"

    dff = datasets[origin].copy()

    # Aplikace filtrů
    if dest != "All":
        dff = dff[dff["destination"] == dest]

    # Filtr letecké společnosti (vícenásobný výběr ze dvou skupin).
    # Pokud nebyla zvolena žádná společnost, ponechá se kompletní dataset
    # v duchu původní volby "All".
    selected_airlines = list(air_trad or []) + list(air_low or [])
    if selected_airlines:
        dff = dff[dff["_airline"].isin(selected_airlines)]

    if dff.empty:
        return _empty_fig("Žádný signál — žádná data pro vybrané filtry"), "—"

    # Výběr sloupce Y podle režimu
    if mode == "avg":
        y_col   = "avg_co2_hr"
        y_label = "Průměrné CO₂ (kg/hod)"
        accent  = NEON_CYAN
    elif mode == "est":
        y_col   = "est_co2_kg"
        y_label = "Odhadované CO₂ (kg/let)"
        accent  = NEON_PINK
    else:  # per_seat
        y_col   = "emissions_per_seat"
        y_label = "Emise/Sedadlo (kg/hod)"
        accent  = NEON_GREEN

    # Odstraní řádky, kde je Y = NaN (zrušené lety)
    dff = dff.dropna(subset=[y_col])

    if dff.empty:
        return _empty_fig(f"Žádný signál — žádná data {y_label} ve výběru"), "—"

    # Vytvoření klíče pro seskupení
    if groupby == "airline":
        dff["_group"] = dff["_airline"]
    elif groupby == "aircraft":
        dff["_group"] = dff["aircraft"]


    fig = go.Figure()
    groups = sorted(dff["_group"].dropna().unique())

    for i, grp in enumerate(groups):
        gdf = dff[dff["_group"] == grp].sort_values("flight_date")
        color = TRACE_COLORS[i % len(TRACE_COLORS)]

        # Bezpečné sestavení polí pro hover
        price_col        = gdf["price"].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )
        airline_col      = gdf["_airline"].fillna("N/A")
        aircraft_col     = gdf["aircraft"].fillna("N/A")
        dest_col         = gdf["destination"].fillna("N/A")
        per_seat_col     = gdf["emissions_per_seat"].apply(
            lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"
        ) if "emissions_per_seat" in gdf.columns else ["N/A"] * len(gdf)

        customdata = list(zip(
            price_col,                                                          # [0]
            airline_col,                                                        # [1]
            aircraft_col,                                                       # [2]
            dest_col,                                                           # [3]
            gdf[y_col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"),# [4]
            per_seat_col                                                        # [5]
        ))

        fig.add_trace(go.Scatter(
            x=gdf["flight_date"],
            y=gdf[y_col],
            mode="lines+markers",
            name=grp,
            line=dict(color=color, width=2),
            marker=dict(
                size=6,
                color=color,
                line=dict(width=1, color=BG_COLOR),
                symbol="circle"
            ),
            customdata=customdata,
            hovertemplate=(
                f"<b>%{{customdata[3]}}  |  %{{x|%d %b %Y}}</b><br>"
                f"<b>{y_label}:</b> %{{customdata[4]}}<br>"
                f"<b>Emise/Sedadlo:</b> %{{customdata[5]}} kg/hod<br>"
                f"<b>Cena letenky:</b> %{{customdata[0]}}<br>"
                f"<b>Letecká společnost:</b> %{{customdata[1]}}<br>"
                f"<b>Typ letadla:</b> %{{customdata[2]}}"
                "<extra></extra>"
            )
        ))

    # Titulek
    dest_part = dest if dest != "All" else "Všechny destinace"
    mode_label = {"avg": "Průměrné CO₂/hod", "est": "Odhadované CO₂/let", "per_seat": "Emise/Sedadlo"}.get(mode, mode)

    groupby_labels = {"airline": "Letecká společnost", "aircraft": "Typ letadla"}
    groupby_cz = groupby_labels.get(groupby, groupby)

    title = (
        f"{origin} → {dest_part}  |  "
        f"<span style='color:{accent}'>{mode_label}</span>  "
        f"|  seskupeno podle: {groupby_cz}"
    )

    fig = _apply_theme(fig, title, y_label, accent)

    # ── Lišta statistik ────────────────────────────────────────────────
    stats_parts = []
    overall_mean   = dff[y_col].mean()
    overall_median = dff[y_col].median()
    overall_min    = dff[y_col].min()
    overall_max    = dff[y_col].max()

    stats_parts.append(
        html.Span([
            html.Span("Statistiky flotily  //  ", style={"color": NEON_BLUE}),
            html.Span(f"Aritmetický průměr: {overall_mean:,.0f}  ", style={"color": NEON_CYAN}),
            html.Span(f"Medián: {overall_median:,.0f}  ", style={"color": NEON_PINK}),
            html.Span(f"Min: {overall_min:,.0f}  ", style={"color": NEON_GREEN}),
            html.Span(f"Max: {overall_max:,.0f}  ", style={"color": NEON_YELLOW}),
            html.Span(f"n={len(dff)}", style={"color": "#555"}),
            html.Span("    //    Za skupinu:  ", style={"color": NEON_BLUE}),
        ])
    )

    for grp in groups:
        gdf  = dff[dff["_group"] == grp]
        gm   = gdf[y_col].mean()
        gmed = gdf[y_col].median()
        stats_parts.append(
            html.Span([
                html.Span(f"{grp} ", style={"color": NEON_CYAN, "fontWeight": "bold"}),
                html.Span(f"μ={gm:,.0f} ", style={"color": TEXT_MUTED}),
                html.Span(f"med={gmed:,.0f}  ", style={"color": "#888"}),
            ])
        )

    return fig, stats_parts


# =====================================================================
# 7. Pomocné funkce pro graf
# =====================================================================
def _empty_fig(msg):
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=NEON_PINK, size=15,
                  family="'Courier New', monospace")
    )
    fig.update_layout(
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_MUTED)
    )
    return fig


def _apply_theme(fig, title, y_label, accent):
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color=accent, size=13, family="Courier New, monospace")
        ),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Courier New, monospace"),
        margin=dict(l=70, r=40, t=60, b=60),
        xaxis=dict(
            title=dict(text="Datum odletu spoje", font=dict(color=NEON_BLUE, size=11)),
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            range=[DATE_START, DATE_END],
            tickformat="%d %b",
            tickfont=dict(color=NEON_BLUE, size=10),
            linecolor="#2a4a4a"
        ),
        yaxis=dict(
            title=dict(text=y_label, font=dict(color=NEON_BLUE, size=11)),
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(color=NEON_BLUE, size=10),
            linecolor="#2a4a4a"
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="#2a4a4a",
            borderwidth=1,
            font=dict(color=TEXT_MUTED, size=11)
        ),
        hovermode="closest"
    )
    return fig


# =====================================================================
# 8. Spuštění
# =====================================================================
# Odeberte nebo zakomentujte:
if __name__ == '__main__':
    app.run(debug=True)
