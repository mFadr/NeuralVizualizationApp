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
    1: "January",  2: "February", 3: "March",     4: "April",
    5: "May",      6: "June",     7: "July",       8: "August",
    9: "September",10: "October", 11: "November",  12: "December"
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
def get_destinations(origin):
    if origin not in datasets or "destination" not in datasets[origin].columns:
        return [{"label": "All", "value": "All"}]
    vals = sorted(datasets[origin]["destination"].dropna().astype(str).unique())
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


def get_airlines(origin, dest):
    if origin not in datasets:
        return [{"label": "All", "value": "All"}]
    df = datasets[origin].copy()
    if dest != "All" and "destination" in df.columns:
        df = df[df["destination"].astype(str) == dest]
    vals = sorted(v for v in df["_airline_col"].dropna().unique() if v and v != "nan")
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


def get_aircraft(origin, dest, airline):
    if origin not in datasets:
        return [{"label": "All", "value": "All"}]
    df = datasets[origin].copy()
    if dest != "All" and "destination" in df.columns:
        df = df[df["destination"].astype(str) == dest]
    if airline != "All":
        df = df[df["_airline_col"] == airline]
    vals = sorted(v for v in df["_aircraft_col"].dropna().unique() if v and v != "nan")
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


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
                "fontFamily":     "Courier New, monospace",
                "backgroundColor": PANEL_BG
            }
        ),
        # Subtle help message below the button
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
    ]),

    # ── Titulek ────────────────────────────────────────────────────────
    html.H2(
        "✈️  NEURAL FLIGHT TRACKER — BOOKING CURVE ANALYZER",
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
            html.Div("◈  FILTERS", style={
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

            html.Div([
                html.Label("ORIGIN", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-origin",
                    options=[{"label": o, "value": o} for o in origins],
                    value=origins[0] if origins else None,
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("DESTINATION", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-dest",
                    value="All",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("AIRLINE", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-airline",
                    value="All",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("AIRCRAFT", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="filter-aircraft",
                    value="All",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "100%"}
                )
            ], style=FILTER_CELL),


        ], style={
            "backgroundColor": PANEL_BG,
            "padding": "16px 18px",
            "borderRadius": "12px",
            "boxShadow": f"0 0 16px {NEON_BLUE}50",
            "width": "12%",
            "flexShrink": "0",
            "overflowY": "auto",
            "overflowX": "visible",
            "marginRight": "20px",
            "position": "relative",
            "zIndex": "9999"
        }),

        # ── Graf (vpravo, 75% width, vyplňuje zbylý prostor) ──────────────────────
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
    Output("filter-airline", "options"),
    Output("filter-airline", "value"),
    Input("filter-origin", "value"),
    Input("filter-dest", "value")
)
def update_airlines(origin, dest):
    return get_airlines(origin, dest), "All"


@app.callback(
    Output("filter-aircraft", "options"),
    Output("filter-aircraft", "value"),
    Input("filter-origin",  "value"),
    Input("filter-dest",    "value"),
    Input("filter-airline", "value")
)
def update_aircraft(origin, dest, airline):
    return get_aircraft(origin, dest, airline), "All"


@app.callback(
    Output("price-chart", "figure"),
    Input("filter-origin",    "value"),
    Input("filter-dest",      "value"),
    Input("filter-airline",   "value"),
    Input("filter-aircraft",  "value")
)
def update_chart(origin, dest, airline, aircraft):
    if origin not in datasets:
        return _empty_fig("NO SIGNAL — dataset not loaded")

    dff = datasets[origin].copy()

    if dest != "All" and "destination" in dff.columns:
        dff = dff[dff["destination"].astype(str) == dest]

    if airline != "All":
        dff = dff[dff["_airline_col"] == airline]

    if aircraft != "All":
        dff = dff[dff["_aircraft_col"] == aircraft]

    if dff.empty:
        return _empty_fig("NO SIGNAL — no flights match selected filters")


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

    return _apply_theme(fig, f"BOOKING CURVE — {origin} → {dest}  |  DAILY")


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
        return _empty_fig("NO SIGNAL — no flight_date data in filtered selection")

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
        f"MONTHLY AGGREGATION — {origin} → {dest}  |  "
        f"MEAN vs MEDIAN  (active: {agg_method.upper()})"
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
