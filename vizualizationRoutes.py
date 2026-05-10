import pandas as pd
import plotly.express as px
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
    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors="coerce"
    )

    # Konverze na datetime
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")

    # Sjednocený sloupec stavu letu (flown / flight canceled / ...).
    # Pokud sloupec ve zdroji chybí, předpokládá se, že všechny záznamy byly odlétnuty.
    if "flown_status" in df.columns:
        df["_status_col"] = df["flown_status"].astype(str).str.lower().str.strip()
    else:
        df["_status_col"] = "flown"

    # Přejmenování sloupců
    df.rename(
        columns={
            "flight_date": "Date",
            "origin": "Origin",
            "destination": "Destination",
            "price": "Price",
        },
        inplace=True,
    )

    return df

# =====================================================================
# 2️⃣ Konfigurace tématu (Cyberpunk styl)
# =====================================================================
BG_COLOR = "#0b0c10"
PANEL_BG = "#1f2833"
NEON_CYAN = "#66fcf1"
NEON_BLUE = "#45a29e"
NEON_PINK = "#ff007f"
TEXT_MUTED = "#c5c6c7"

# Barvy pro vodorovné sloupcové grafy
TRUE_PURPLE = "#9D4EDD"      # 1. graf (10 nejlevnějších)
ELECTRIC_PURPLE = "#7209B7"  # 2. graf (10 nejdražších)
CHART_CYAN = "#00D9FF"       # 3. graf (porovnání výchozích letišť)

# =====================================================================
# 3️⃣ Pomocné funkce
# =====================================================================
def _apply_status_filter(df, status):
    """
    Filtr podle stavu letu (data scope switcher).
      status == "flown"  → pouze skutečně odlétnuté lety
      status == "all"    → všechny záznamy včetně zrušených letů
    """
    if status == "flown" and "_status_col" in df.columns:
        return df[df["_status_col"] == "flown"]
    return df


def interpolate_color(color1, color2, factor):
    """Lineární interpolace mezi dvěma barvami v hex formátu."""
    c1_rgb = tuple(int(color1[i:i + 2], 16) for i in (1, 3, 5))
    c2_rgb = tuple(int(color2[i:i + 2], 16) for i in (1, 3, 5))
    result = tuple(int(c1_rgb[i] + (c2_rgb[i] - c1_rgb[i]) * factor) for i in range(3))
    return '#{:02x}{:02x}{:02x}'.format(*result)


def get_color_gradient(values, dark_color, light_color):
    """Vytvoří barevný přechod podle vstupních hodnot (0=tmavá, 1=světlá)."""
    if not values:
        return []
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    colors = []
    for val in values:
        factor = (val - min_val) / range_val
        colors.append(interpolate_color(dark_color, light_color, factor))
    return colors


def calculate_route_analytics(datasets, status="all", agg_method="mean"):
    """Vypočítá agregovanou cenu (průměr nebo medián) pro všechny trasy
    napříč všemi datasety. Volitelně lze omezit pouze na uskutečněné lety."""
    route_prices = {}

    for origin_code, df in datasets.items():
        df = _apply_status_filter(df, status)
        for destination in df['Destination'].dropna().unique():
            route_data = df[df['Destination'] == destination]
            if route_data.empty:
                continue
            if agg_method == "median":
                value = route_data['Price'].median()
            else:
                value = route_data['Price'].mean()
            if pd.notna(value):
                route_prices[f"{origin_code}-{destination}"] = value

    return route_prices


# =====================================================================
# 4️⃣ Rozložení
# =====================================================================
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

# Panel se systémovými parametry (kompaktní řádkové uspořádání)
_system_panel = html.Div([
    html.H3(
        "SYSTÉMOVÉ PARAMETRY",
        style={
            "color": NEON_BLUE,
            "borderBottom": f"1px solid {NEON_BLUE}",
            "paddingBottom": "10px",
            "marginTop": 0
        }
    ),
    html.Div([
        # Filtr zrušených letů
        html.Div([
            html.Label("Filtr zrušených letů", style={"color": TEXT_MUTED, "fontSize": "12px"}),
            dcc.RadioItems(
                id="filter-status-routes",
                options=[
                    {"label": "  Zahrnout i zrušené lety", "value": "all"},
                    {"label": "  Pouze uskutečněné lety", "value": "flown"}
                ],
                value="all",
                labelStyle={
                    "display": "block",
                    "color": NEON_CYAN,
                    "fontSize": "13px",
                    "marginBottom": "4px"
                },
                inputStyle={"marginRight": "6px", "accentColor": NEON_CYAN},
                style={"marginTop": "6px"}
            )
        ], style={"flex": "1", "minWidth": "240px", "marginRight": "30px"}),

        # Agregační metoda
        html.Div([
            html.Label("Agregační metoda", style={"color": TEXT_MUTED, "fontSize": "12px"}),
            dcc.RadioItems(
                id="agg-method-routes",
                options=[
                    {"label": "  Aritmetický průměr", "value": "mean"},
                    {"label": "  Medián", "value": "median"}
                ],
                value="mean",
                labelStyle={
                    "display": "inline-block",
                    "color": NEON_CYAN,
                    "marginRight": "16px",
                    "fontSize": "13px"
                },
                inputStyle={"marginRight": "6px", "accentColor": NEON_CYAN},
                style={"marginTop": "6px"}
            )
        ], style={"flex": "1", "minWidth": "240px"})
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "10px"})
], style={
    "backgroundColor": PANEL_BG,
    "padding": "20px",
    "borderRadius": "15px",
    "boxShadow": f"0 0 20px {NEON_BLUE}60",
    "marginBottom": "30px"
})

layout = html.Div([
    _back_btn,
    html.H2(
        "Analýza tras dle přímého porovnání cenových úrovní výchozích letišť",
        style={
            "textAlign": "center",
            "textShadow": f"0 0 10px {NEON_CYAN}",
            "letterSpacing": "3px",
            "marginBottom": "30px"
        }
    ),

    _system_panel,

    # 📊 SPODNÍ VODOROVNÉ SLOUPCOVÉ GRAFY (3 v jednom řádku)
    html.Div([
        # Graf 1: 10 Nejlevnějších tras
        html.Div([
            html.Div([
                html.Label("Filtry destinací:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist-cheapest-routes",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={
                        "color": "white",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "marginRight": "15px"
                    }
                ),
            ], style={
                "backgroundColor": "#333333",
                "padding": "10px",
                "borderRadius": "10px",
                "marginBottom": "10px"
            }),
            dcc.Graph(id="cheapest-routes-chart-routes")
        ], style={
            "flex": "1",
            "borderRadius": "15px",
            "overflow": "hidden",
            "boxShadow": f"0 0 15px {TRUE_PURPLE}80"
        }),

        # Graf 2: 10 Nejdražších tras
        html.Div([
            html.Div([
                html.Label("Filtry destinací:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist-expensive-routes",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={
                        "color": "white",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "marginRight": "15px"
                    }
                ),
            ], style={
                "backgroundColor": "#333333",
                "padding": "10px",
                "borderRadius": "10px",
                "marginBottom": "10px"
            }),
            dcc.Graph(id="expensive-routes-chart-routes")
        ], style={
            "flex": "1",
            "borderRadius": "15px",
            "overflow": "hidden",
            "boxShadow": f"0 0 15px {ELECTRIC_PURPLE}80"
        }),

        # Graf 3: Srovnání výchozích letišť s filtry destinací
        html.Div([
            html.Div([
                html.Label("Filtry destinací:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                dcc.Checklist(
                    id="destination-checklist-routes",
                    options=[
                        {'label': ' AMS', 'value': 'AMS'},
                        {'label': ' BCN', 'value': 'BCN'},
                        {'label': ' FCO', 'value': 'FCO'},
                        {'label': ' LON', 'value': 'LON'}
                    ],
                    value=['AMS', 'BCN', 'FCO', 'LON'],
                    inline=True,
                    labelStyle={
                        "color": "white",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "marginRight": "15px"
                    }
                ),
            ], style={
                "backgroundColor": "#333333",
                "padding": "10px",
                "borderRadius": "10px",
                "marginBottom": "10px"
            }),
            dcc.Graph(id="origin-comparison-chart-routes")
        ], style={
            "flex": "1",
            "borderRadius": "15px",
            "overflow": "hidden",
            "boxShadow": f"0 0 15px {CHART_CYAN}80"
        })
    ], style={"display": "flex", "gap": "20px", "marginTop": "10px"})

], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "30px",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
})

# =====================================================================
# 5️⃣ Callbacky pro tři vodorovné sloupcové grafy
# =====================================================================
@app.callback(
    Output("cheapest-routes-chart-routes", "figure"),
    Input("destination-checklist-cheapest-routes", "value"),
    Input("filter-status-routes", "value"),
    Input("agg-method-routes", "value")
)
def update_cheapest_routes(selected_destinations, status, agg_method):
    route_prices = calculate_route_analytics(datasets, status, agg_method)

    # Filtruj podle vybraných destinací
    if selected_destinations:
        filtered_routes = {
            k: v for k, v in route_prices.items()
            if k.split('-')[1] in selected_destinations
        }
    else:
        filtered_routes = route_prices

    # 10 nejlevnějších, levnější vrch
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1])[:10]
    sorted_routes.reverse()
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    colors = get_color_gradient(prices, '#ffffff', '#3d1a4d')

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

    metric = "Medián" if agg_method == "median" else "Průměr"
    fig.update_layout(
        title=f"10 Nejlevnějších leteckých linek ({metric})",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Cena ($)"),
        yaxis=dict(showgrid=False, title="Letecké linky"),
        height=400
    )
    return fig


@app.callback(
    Output("expensive-routes-chart-routes", "figure"),
    Input("destination-checklist-expensive-routes", "value"),
    Input("filter-status-routes", "value"),
    Input("agg-method-routes", "value")
)
def update_expensive_routes(selected_destinations, status, agg_method):
    route_prices = calculate_route_analytics(datasets, status, agg_method)

    if selected_destinations:
        filtered_routes = {
            k: v for k, v in route_prices.items()
            if k.split('-')[1] in selected_destinations
        }
    else:
        filtered_routes = route_prices

    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_routes.reverse()
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    colors = get_color_gradient(prices, '#6b0080', '#e6b3ff')

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

    metric = "Medián" if agg_method == "median" else "Průměr"
    fig.update_layout(
        title=f"10 Nejdražších leteckých linek ({metric})",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Cena ($)"),
        yaxis=dict(showgrid=False, title="Letecké linky"),
        height=400
    )
    return fig


@app.callback(
    Output("origin-comparison-chart-routes", "figure"),
    Input("destination-checklist-routes", "value"),
    Input("filter-status-routes", "value"),
    Input("agg-method-routes", "value")
)
def update_origin_comparison(selected_destinations, status, agg_method):
    origin_prices = {}

    for origin_code, df in datasets.items():
        df = _apply_status_filter(df, status)
        if selected_destinations:
            filtered_df = df[df['Destination'].isin(selected_destinations)]
        else:
            filtered_df = df

        if not filtered_df.empty:
            if agg_method == "median":
                value = filtered_df['Price'].median()
            else:
                value = filtered_df['Price'].mean()
            if pd.notna(value):
                origin_prices[origin_code] = value

    origins = list(origin_prices.keys())
    prices = list(origin_prices.values())

    colors = get_color_gradient(prices, '#003d4d', '#99e6f0')

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

    metric = "Medián" if agg_method == "median" else "Průměr"
    fig.update_layout(
        title=f"Porovnání cenových úrovní výchozích letišť ({metric})",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Cena ($)"),
        yaxis=dict(showgrid=False, title="Výchozí letiště"),
        height=400
    )
    return fig

# =====================================================================
# 6️⃣ Načítání datasetů (na úrovni modulu)
# =====================================================================
print("Loading datasets for routes view...")
datasets = {}
for origin_code, file_path in DATASET_PATHS.items():
    try:
        df = load_data_from_file(file_path)
        datasets[origin_code] = df
        print(f"✓ Loaded {origin_code}: {len(df)} records")
    except Exception as e:
        print(f"✗ Error loading {origin_code} from {file_path}: {e}")

if not datasets:
    print("WARNING: No datasets loaded — routes view will show empty state.")

print(f"\n✓ Successfully loaded {len(datasets)} datasets for routes view\n")

# =====================================================================
# 7️⃣ Vstupní bod (pouze pro místní vývoj)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8058))
    app.run(host="0.0.0.0", port=port, debug=False)
