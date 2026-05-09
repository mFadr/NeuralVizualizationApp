import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from app_instance import app

# ============================================================a=========
# 1. Konfigurace
# =====================================================================
from config import DATASET_PATHS

# =====================================================================
# 2. Cyberpunk téma
# =====================================================================
BG_COLOR       = "#0b0c10"
PANEL_BG       = "#1f2833"
NEON_CYAN      = "#66fcf1"
NEON_BLUE      = "#45a29e"
NEON_PINK      = "#ff007f"
NEON_YELLOW    = "#f5c518"
TEXT_MUTED     = "#c5c6c7"
DROPDOWN_STYLE = {"color": "black"}

MONTH_NAMES = {
    1: "Leden",     2: "Únor",     3: "Březen",    4: "Duben",
    5: "Květen",    6: "Červen",   7: "Červenec",  8: "Srpen",
    9: "Září",     10: "Říjen",   11: "Listopad", 12: "Prosinec"
}

# =====================================================================
# Pevný seznam dat odletu (Leden 2026) s českými zkratkami dnů v týdnu
# =====================================================================
WEEKDAY_ABBR_CZ = {0: "PO", 1: "ÚT", 2: "ST", 3: "ČT", 4: "PÁ", 5: "SO", 6: "NE"}


def _build_departure_date_options():
    """Sestaví pevný seznam možností pro filtr data odletu (1.–31. leden 2026).

    Vrací seznam slovníků pro dcc.Dropdown ve formátu
    [{"label": "2026-01-01 : ČT", "value": "2026-01-01"}, ...]
    s úvodní položkou "Vše".
    """
    options = [{"label": "Vše", "value": "All"}]
    for day in range(1, 32):
        date = pd.Timestamp(year=2026, month=1, day=day)
        weekday_cz = WEEKDAY_ABBR_CZ[date.weekday()]
        date_str = date.strftime("%Y-%m-%d")
        options.append({
            "label": f"{date_str} : {weekday_cz}",
            "value": date_str
        })
    return options


DEPARTURE_DATE_OPTIONS = _build_departure_date_options()

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
    "marginTop": "8px",
    "marginBottom": "4px",
    "display": "block"
}

# =====================================================================
# 3. Načítání dat
# =====================================================================
def load_data(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")
    df.columns = df.columns.str.strip().str.lower()

    required = ['search_date', 'flight_date', 'price']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.dropna(subset=required)

    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors='coerce'
    )
    df["search_date"] = pd.to_datetime(df["search_date"], errors='coerce')
    df["flight_date"]  = pd.to_datetime(df["flight_date"],  errors='coerce')
    df = df.dropna(subset=['price', 'search_date', 'flight_date'])

    # Odvodí měsíc z flight_date dynamicky, bez natvrdo zadaného seznamu
    df["flight_month"] = df["flight_date"].dt.month

    # Sjednocený sloupec aerolinky bez ohledu na pojmenování ve zdroji
    airline_col = next(
        (c for c in ['airline_details', 'airline'] if c in df.columns), None
    )
    df["_airline_col"]   = df[airline_col].astype(str) if airline_col else ""
    df["_aircraft_col"] = df["aircraft"].astype(str) if "aircraft" in df.columns else ""

    # Sjednocený sloupec stavu letu (flown / flight canceled / ...).
    # Pokud sloupec ve zdroji chybí, předpokládá se, že všechny záznamy byly odlétnuty.
    if "flown_status" in df.columns:
        df["_status_col"] = df["flown_status"].astype(str).str.lower().str.strip()
    else:
        df["_status_col"] = "flown"

    return df


print("Loading datasets...")
datasets = {}
for code, path in DATASET_PATHS.items():
    try:
        datasets[code] = load_data(path)
        months_present = sorted(datasets[code]["flight_month"].unique())
        month_labels   = [MONTH_NAMES.get(m, str(m)) for m in months_present]
        print(f"✓ {code}: {len(datasets[code])} records | months in data: {month_labels}")
    except Exception as e:
        print(f"✗ {code}: {e}")

origins = list(datasets.keys())

# =====================================================================
# 4. Pomocné funkce
# =====================================================================
def _apply_status(df, status):
    """
    Filtr podle stavu letu.
      status == "flown"  → pouze skutečně odlétnuté lety
      status == "all"    → všechny záznamy včetně zrušených letů
    """
    if status == "flown" and "_status_col" in df.columns:
        return df[df["_status_col"] == "flown"]
    return df


def get_destinations(origin):
    if origin not in datasets or "destination" not in datasets[origin].columns:
        return [{"label": "All", "value": "All"}]
    vals = sorted(datasets[origin]["destination"].dropna().astype(str).unique())
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


# =====================================================================
# Pomocné funkce pro klasifikaci aerolinek (Tradiční vs. Nízkonákladové)
# =====================================================================
def _airline_matches(value, target_name):
    """Posoudí, zda hodnota ze sloupce aerolinka odpovídá cílovému názvu společnosti.

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


def get_available_airlines(origin, dest, status="all"):
    """Vrátí seznam unikátních aerolinek dostupných pro danou trasu.

    Vrací holý seznam názvů použitelný pro split_airlines_by_type
    (na rozdíl od formátu options pro dropdown / checklist).
    """
    if origin not in datasets:
        return []
    df = datasets[origin].copy()
    df = _apply_status(df, status)
    if dest != "All" and "destination" in df.columns:
        df = df[df["destination"].astype(str) == dest]
    return sorted(v for v in df["_airline_col"].dropna().unique() if v and v != "nan")


# =====================================================================
# 5. Rozložení — jednoradková lišta filtrů + graf přes plnou šířku
# =====================================================================
LABEL_STYLE = {
    "color": NEON_BLUE,
    "fontSize": "10px",
    "letterSpacing": "1px",
    "marginBottom": "4px",
    "display": "block"
}
FILTER_CELL = {
    "display": "block",
    "marginBottom": "14px",
    "width": "100%"
}

layout = html.Div([

    # ── Tlačítko zpět + Nápověda (Refresh Tip) ──────────────────────────
    html.Div([
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
                "fontFamily":     "Courier New, monospace",
                "backgroundColor": PANEL_BG
            }
        ),
        # Subtle help message below the button
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
    ]),

    # ── Titulek ────────────────────────────────────────────────────────
    html.H2(
        "✈️  NEURAL FLIGHT TRACKER — Křivky jednotlivých rezervací",
        style={
            "textAlign": "center",
            "color": NEON_CYAN,
            "textShadow": f"0 0 12px {NEON_CYAN}",
            "letterSpacing": "3px",
            "margin": "0 0 8px 0",
            "fontSize": "17px"
        }
    ),

    # ── Hlavní flex layout: Sidebar filtrů (vlevo) + Graf (vpravo) ──────────
    html.Div([
        # ── Sidebar filtrů (banner vlevo, 25% width) ──────────────────────────
        html.Div([
            # Hlavička sidebaru
            html.Div("◈  Filtry", style={
                "color": NEON_CYAN,
                "fontSize": "11px",
                "letterSpacing": "3px",
                "fontWeight": "bold",
                "fontFamily": "Courier New, monospace",
                "marginBottom": "16px",
                "paddingBottom": "10px",
                "borderBottom": f"1px solid {NEON_BLUE}30",
                "textShadow": f"0 0 8px {NEON_CYAN}"
            }),

            # ── Přepínač datového rozsahu (zrušené lety ANO/NE) ───────────
            html.Div([
                html.Label("Filtr zrušených letů", style=LABEL_STYLE),
                dcc.RadioItems(
                    id="filter-status",
                    options=[
                        {"label": " Zahrnout i zrušené lety",    "value": "all"},
                        {"label": " Pouze uskutečněné lety",   "value": "flown"},
                    ],
                    value="all",
                    labelStyle={
                        "display": "block",
                        "color": TEXT_MUTED,
                        "fontSize": "10px",
                        "marginBottom": "4px",
                        "cursor": "pointer",
                        "fontFamily": "Courier New, monospace",
                        "letterSpacing": "1px"
                    },
                    inputStyle={
                        "marginRight": "6px",
                        "accentColor": NEON_CYAN
                    }
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("Výchozí letiště", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-origin",
                    options=[{"label": o, "value": o} for o in origins],
                    value=origins[0] if origins else None,
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("Destinace", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-dest",
                    value="All",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("Datum odletu spoje", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-departure-date",
                    options=DEPARTURE_DATE_OPTIONS,
                    value="All",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

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
                        "marginTop": "4px",
                        "marginBottom": "4px",
                        "display": "block",
                        "lineHeight": "1.2"
                    },
                    inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE
                ),
                # Skupiny pod sebou: Tradiční nahoře, Nízkonákladové dole
                html.Div([
                    html.Label("Tradiční společnosti", style=AIRLINE_GROUP_HEADER_STYLE),
                    dcc.Checklist(
                        id="airline-traditional",
                        options=[],
                        value=[],
                        labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                        inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                        style=AIRLINE_CHECKLIST_STYLE
                    ),
                    html.Label("Nízkonákladové společnosti", style=AIRLINE_GROUP_HEADER_STYLE),
                    dcc.Checklist(
                        id="airline-lowcost",
                        options=[],
                        value=[],
                        labelStyle=AIRLINE_CHECKLIST_LABEL_STYLE,
                        inputStyle=AIRLINE_CHECKLIST_INPUT_STYLE,
                        style=AIRLINE_CHECKLIST_STYLE
                    )
                ])
            ], style=FILTER_CELL),


        ], style={
            "backgroundColor": PANEL_BG,
            "padding": "16px 18px",
            "borderRadius": "12px",
            "boxShadow": f"0 0 16px {NEON_BLUE}50",
            "width": "10%",
            "flexShrink": "0",
            "overflowY": "auto",
            "overflowX": "visible",
            "marginRight": "20px",
            "position": "relative",
            "zIndex": "9999"
        }),

        # ── Graf (vpravo, vyplňuje zbylý prostor) ──────────────────────
        html.Div([
            dcc.Graph(
                id="price-chart",
                style={"height": "100%", "width": "100%"},
                config={"displayModeBar": True, "responsive": True}
            )
        ], style={
            "borderRadius": "15px",
            "overflow": "hidden",
            "boxShadow": f"0 0 20px {NEON_CYAN}40",
            "flex": "1",
            "minWidth": "0",
            "minHeight": "0",
            "position": "relative",
            "zIndex": "1"
        })

    ], style={
        "display": "flex",
        "gap": "20px",
        "width": "100%",
        "flex": "1",
        "minHeight": "0"
    })

], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "padding": "12px 22px",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "boxSizing": "border-box",
    "display": "flex",
    "flexDirection": "column",
    "height": "100vh",
    "overflow": "hidden"
})
# =====================================================================
# 6. Callbacky
# =====================================================================
@app.callback(
    Output("filter-dest", "options"),
    Output("filter-dest", "value"),
    Input("filter-origin", "value")
)
def update_destinations(origin):
    opts = get_destinations(origin)
    default = opts[1]["value"] if len(opts) > 1 else "All"
    return opts, default


@app.callback(
    Output("airline-traditional", "options"),
    Output("airline-traditional", "value"),
    Output("airline-lowcost", "options"),
    Output("airline-lowcost", "value"),
    Input("filter-origin",  "value"),
    Input("filter-dest",    "value"),
    Input("filter-status",  "value"),
    Input("airline-select-all", "value")
)
def update_airlines(origin, dest, status, select_all):
    available = get_available_airlines(origin, dest, status)
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
    Output("price-chart", "figure"),
    Input("filter-origin",         "value"),
    Input("filter-dest",           "value"),
    Input("airline-traditional",   "value"),
    Input("airline-lowcost",       "value"),
    Input("filter-departure-date", "value"),
    Input("filter-status",         "value")
)
def update_chart(origin, dest, air_trad, air_low, departure_date, status):
    if origin not in datasets:
        return _empty_fig("ŽÁDNÝ SIGNÁL — dataset není načten")

    dff = datasets[origin].copy()

    # Filtr stavu letu (s/bez zrušených letů)
    dff = _apply_status(dff, status)

    if dest != "All" and "destination" in dff.columns:
        dff = dff[dff["destination"].astype(str) == dest]

    # Filtr letecké společnosti (vícenásobný výběr ze dvou skupin).
    # Pokud nebyla zvolena žádná společnost, ponechá se kompletní dataset
    # v duchu původní volby "All".
    selected_airlines = list(air_trad or []) + list(air_low or [])
    if selected_airlines:
        dff = dff[dff["_airline_col"].isin(selected_airlines)]

    # Filtr data odletu (jeden vybraný datum nebo "Vše").
    # Sloupec flight_date je pandas datetime, hodnota z dropdownu je řetězec
    # ve formátu YYYY-MM-DD; porovnává se proto datová část (date()).
    if departure_date and departure_date != "All":
        try:
            target_date = pd.to_datetime(departure_date).date()
            dff = dff[dff["flight_date"].dt.date == target_date]
        except (ValueError, TypeError):
            pass

    if dff.empty:
        return _empty_fig("ŽÁDNÝ SIGNÁL — žádné lety neodpovídají vybraným filtrům")


    return _build_daily_chart(dff, origin, dest)


# =====================================================================
# 7. Sestavení grafů
# =====================================================================
def _empty_fig(msg):
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=NEON_PINK, size=16)
    )
    return _apply_theme(fig, msg)


def _apply_theme(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(color=NEON_CYAN, size=14)),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=60, r=40, t=55, b=55),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False,
                   tickprefix="$"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#333"),
        hovermode="x unified"
    )
    return fig


def _build_daily_chart(dff, origin, dest):
    """
    Denní režim — jedna čára pro každé datum odletu.
    X = datum pozorování/vyhledání, Y = cena, barva = datum odletu letu.
    """
    dff = dff.copy()
    dff["flight_date_str"] = dff["flight_date"].dt.strftime("%Y-%m-%d")

    fig = go.Figure()
    for fdate, grp in dff.groupby("flight_date_str"):
        grp = grp.sort_values("search_date")
        fig.add_trace(go.Scatter(
            x=grp["search_date"],
            y=grp["price"],
            mode="lines+markers",
            name=fdate,
            customdata=grp[["_airline_col", "_aircraft_col"]].values,
            hovertemplate=(
                "<b>Obs. date:</b> %{x|%b %d, %Y}<br>"
                "<b>Price:</b> $%{y:.2f}<br>"
                "<b>Airline:</b> %{customdata[0]}<br>"
                "<b>Aircraft:</b> %{customdata[1]}"
                "<extra></extra>"
            ),
            marker=dict(size=5),
            line=dict(width=2)
        ))

    return _apply_theme(fig, f"KŘIVKA REZERVACÍ — {origin} → {dest}  |  DENNÍ")


def _build_monthly_chart(dff, origin, dest, agg_method):
    """
    Měsíční režim — agreguje ceny přes všechny měsíce, které jsou
    přítomné ve filtrovaných datech. Bez natvrdo zadaného seznamu
    měsíců, funguje pro libovolný rozsah dat.

    Vykreslí se jak průměr (Mean), tak medián (Median). Vybraná agregace
    je zvýrazněná (silnější plná čára, větší značky), druhá je tlumená
    tečkovaná čára. Poznámka Δ ukazuje rozdíl pro každý měsíc.
    """
    dff = dff.copy()

    # Všechny měsíce skutečně přítomné v tomto filtrovaném výřezu, chronologicky seřazené
    available_months = sorted(dff["flight_month"].dropna().unique().astype(int))

    if not available_months:
        return _empty_fig("ŽÁDNÝ SIGNÁL — žádná data flight_date v gefiltrovém výběru")

    # Agregace po měsících přes celý filtrovaný výřez
    agg = (
        dff.groupby("flight_month")["price"]
        .agg(mean_price="mean", median_price="median", count="count")
        .reindex(available_months)
        .reset_index()
    )
    agg["month_name"] = agg["flight_month"].map(
        lambda m: MONTH_NAMES.get(int(m), str(m))
    )

    fig = go.Figure()

    # ── Průměr ─────────────────────────────────────────────────────────
    mean_on = agg_method == "mean"
    fig.add_trace(go.Scatter(
        x=agg["month_name"],
        y=agg["mean_price"],
        mode="lines+markers",
        name="Mean price",
        line=dict(
            color=NEON_CYAN if mean_on else "#1a4a48",
            width=3 if mean_on else 1.5,
            dash="solid" if mean_on else "dot"
        ),
        marker=dict(
            size=10 if mean_on else 5,
            color=NEON_CYAN if mean_on else "#1a4a48",
            line=dict(width=2, color=BG_COLOR)
        ),
        customdata=agg[["count"]].values,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<b>Mean:</b> $%{y:.2f}<br>"
            "<b>Observations:</b> %{customdata[0]}<br>"
            "<extra></extra>"
        )
    ))

    # ── Medián ─────────────────────────────────────────────────────────
    med_on = agg_method == "median"
    fig.add_trace(go.Scatter(
        x=agg["month_name"],
        y=agg["median_price"],
        mode="lines+markers",
        name="Median price",
        line=dict(
            color=NEON_PINK if med_on else "#5a0030",
            width=3 if med_on else 1.5,
            dash="solid" if med_on else "dot"
        ),
        marker=dict(
            size=10 if med_on else 5,
            color=NEON_PINK if med_on else "#5a0030",
            line=dict(width=2, color=BG_COLOR)
        ),
        customdata=agg[["count"]].values,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<b>Median:</b> $%{y:.2f}<br>"
            "<b>Observations:</b> %{customdata[0]}<br>"
            "<extra></extra>"
        )
    ))

    # ── Poznámky k rozdílu Δ ───────────────────────────────────────────
    for _, row in agg.iterrows():
        if pd.notna(row["mean_price"]) and pd.notna(row["median_price"]):
            diff = abs(row["mean_price"] - row["median_price"])
            top  = max(row["mean_price"], row["median_price"])
            fig.add_annotation(
                x=row["month_name"],
                y=top,
                text=f"Δ ${diff:.0f}",
                showarrow=False,
                yshift=16,
                font=dict(color=NEON_YELLOW, size=10)
            )

    fig = _apply_theme(
        fig,
        f"AGREGACE MĚSÍCE — {origin} → {dest}  |  "
        f"PRŮMĚR vs MEDIÁN  (aktivní: {agg_method.upper()})"
    )

    # Uzamkne osu X na chronologické pořadí měsíců přítomných v datech
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=agg["month_name"].tolist()
    )

    return fig


# =====================================================================
# 8. Vstupní bod (jen pro lokální vývoj)
# =====================================================================
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)