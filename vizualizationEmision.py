import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import sys

# =====================================================================
# 1. Configuration
# =====================================================================
from config import DATASET_PATHS

# X-axis date range — fixed to January 2026
DATE_START = pd.Timestamp("2026-01-01")
DATE_END   = pd.Timestamp("2026-01-31")

# =====================================================================
# 2. Cyberpunk Theme
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

# Colour palette for traces (airlines/routes get cycled through these)
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
# 3. Data Loading
# =====================================================================
def load_data(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(".", "_", regex=False)

    # Normalise key column names
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

    # Also handle the exact column names from the sample header
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

    # Parse dates
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")
    df["flight_date"]  = pd.to_datetime(df["flight_date"],  errors="coerce")
    df = df.dropna(subset=["search_date", "flight_date"])

    # Filter to Jan 2026 flight dates only
    df = df[(df["flight_date"] >= DATE_START) & (df["flight_date"] <= DATE_END)]

    # Parse price
    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors="coerce"
    )

    # Parse CO2 columns — replace string 'Flight Canceled' with NaN for numeric ops
    for col in ["est_co2_kg", "avg_co2_hr", "est_fuel_kg", "emissions_per_seat_(avg)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    # Normalise emissions_per_seat column name (semicolon sep may vary spacing)
    for col in list(df.columns):
        if "emission" in col and "seat" in col:
            df.rename(columns={col: "emissions_per_seat"}, inplace=True)
            break
    if "emissions_per_seat" not in df.columns:
        df["emissions_per_seat"] = np.nan

    # Ensure helper columns exist
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


print("Loading datasets...")
datasets = {}
for code, path in DATASET_PATHS.items():
    try:
        datasets[code] = load_data(path)
        n = len(datasets[code])
        print(f"✓ {code}: {n} records in Jan 2026")
    except Exception as e:
        print(f"✗ {code}: {e}")

if not datasets:
    print("⚠️  WARNING: No datasets loaded. Creating placeholder datasets...")
    datasets = {code: pd.DataFrame() for code in DATASET_PATHS.keys()}

origins = list(datasets.keys())

# =====================================================================
# 4. Helpers
# =====================================================================
def get_destinations(origin):
    if origin not in datasets:
        return [{"label": "All", "value": "All"}]
    vals = sorted(datasets[origin]["destination"].dropna().unique())
    vals = [v for v in vals if v and v != "nan"]
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


def get_airlines(origin, dest):
    if origin not in datasets:
        return [{"label": "All", "value": "All"}]
    df = datasets[origin].copy()
    if dest != "All":
        df = df[df["destination"] == dest]
    vals = sorted(v for v in df["_airline"].dropna().unique() if v and v != "nan")
    return [{"label": "All", "value": "All"}] + [{"label": v, "value": v} for v in vals]


# =====================================================================
# 5. Layout
# =====================================================================
from main_page import app  # share the single server instance
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

    # ── Scanline overlay (purely decorative CSS) ──────────────────────
    html.Div(style={
        "position": "fixed", "top": 0, "left": 0,
        "width": "100%", "height": "100%",
        "backgroundImage": "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        "pointerEvents": "none", "zIndex": 9999
    }),

    # ── Title ─────────────────────────────────────────────────────────
    html.Div([
        html.Div("◈", style={
            "color": NEON_CYAN, "fontSize": "28px",
            "display": "inline-block", "marginRight": "14px",
            "verticalAlign": "middle",
            "filter": f"drop-shadow(0 0 8px {NEON_CYAN})"
        }),
        html.H2("EMISSION INTELLIGENCE SYSTEM", style={
            "display": "inline-block",
            "color": NEON_CYAN,
            "textShadow": f"0 0 20px {NEON_CYAN}, 0 0 40px {NEON_CYAN}40",
            "letterSpacing": "5px",
            "fontSize": "18px",
            "margin": 0,
            "fontFamily": "'Courier New', monospace",
            "verticalAlign": "middle"
        }),
        html.Div("◈", style={
            "color": NEON_CYAN, "fontSize": "28px",
            "display": "inline-block", "marginLeft": "14px",
            "verticalAlign": "middle",
            "filter": f"drop-shadow(0 0 8px {NEON_CYAN})"
        }),
        html.Div("CARBON FOOTPRINT TRACKER  //  JANUARY 2026", style={
            "color": NEON_BLUE,
            "fontSize": "10px",
            "letterSpacing": "4px",
            "marginTop": "4px",
            "fontFamily": "'Courier New', monospace"
        })
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    # ── Filter Bar ────────────────────────────────────────────────────
    html.Div([


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

        # Origin
        html.Div([
            html.Label("ORIGIN", style=LABEL_STYLE),
            dcc.Dropdown(
                id="em-origin",
                options=[{"label": o, "value": o} for o in origins],
                value=origins[0],
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "100px"}
            )
        ], style=FILTER_CELL),

        # Destination
        html.Div([
            html.Label("DESTINATION", style=LABEL_STYLE),
            dcc.Dropdown(
                id="em-dest",
                value="All",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "120px"}
            )
        ], style=FILTER_CELL),

        # Airline
        html.Div([
            html.Label("AIRLINE", style=LABEL_STYLE),
            dcc.Dropdown(
                id="em-airline",
                value="All",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "170px"}
            )
        ], style=FILTER_CELL),

        DIVIDER,

        # Viz mode
        html.Div([
            html.Label("EMISSION MODE", style=LABEL_STYLE),
            dcc.RadioItems(
                id="em-mode",
                options=[
                    {"label": "  AVG CO₂  (kg/hr)",        "value": "avg"},
                    {"label": "  Est. CO₂  (kg/flight)",   "value": "est"},
                    {"label": "  Emission / Seat  (kg/hr)", "value": "per_seat"}
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

        # Group-by
        html.Div([
            html.Label("GROUP TRACES BY", style=LABEL_STYLE),
            dcc.RadioItems(
                id="em-groupby",
                options=[
                    {"label": "  Airline",  "value": "airline"},
                    {"label": "  Aircraft", "value": "aircraft"},
                    {"label": "  Route",    "value": "route"}
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

    # ── Stats row ─────────────────────────────────────────────────────
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

    # ── Chart ─────────────────────────────────────────────────────────
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
    })

], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "22px 26px",
    "fontFamily": "'Courier New', monospace",
    "boxSizing": "border-box"
})

# =====================================================================
# 6. Callbacks
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
    Output("em-airline", "options"),
    Output("em-airline", "value"),
    Input("em-origin",   "value"),
    Input("em-dest",     "value")
)
def update_airline(origin, dest):
    return get_airlines(origin, dest), "All"


@app.callback(
    Output("em-chart",  "figure"),
    Output("em-stats",  "children"),
    Input("em-origin",  "value"),
    Input("em-dest",    "value"),
    Input("em-airline", "value"),
    Input("em-mode",    "value"),
    Input("em-groupby", "value")
)
def update_chart(origin, dest, airline, mode, groupby):

    if origin not in datasets:
        return _empty_fig("NO SIGNAL — dataset not loaded"), "—"

    dff = datasets[origin].copy()

    # Apply filters
    if dest != "All":
        dff = dff[dff["destination"] == dest]
    if airline != "All":
        dff = dff[dff["_airline"] == airline]

    if dff.empty:
        return _empty_fig("NO SIGNAL — no data for selected filters"), "—"

    # Pick the Y column based on mode
    if mode == "avg":
        y_col   = "avg_co2_hr"
        y_label = "AVG CO₂ (kg/hr)"
        accent  = NEON_CYAN
    elif mode == "est":
        y_col   = "est_co2_kg"
        y_label = "Est. CO₂ (kg/flight)"
        accent  = NEON_PINK
    else:  # per_seat
        y_col   = "emissions_per_seat"
        y_label = "Emission/Seat (kg/hr)"
        accent  = NEON_GREEN

    # Drop rows where Y is NaN (canceled flights)
    dff = dff.dropna(subset=[y_col])

    if dff.empty:
        return _empty_fig(f"NO SIGNAL — no {y_label} data in selection"), "—"

    # Build group key
    if groupby == "airline":
        dff["_group"] = dff["_airline"]
    elif groupby == "aircraft":
        dff["_group"] = dff["aircraft"]
    else:  # route
        dff["_group"] = dff["destination"].apply(lambda d: f"{origin}→{d}")

    fig = go.Figure()
    groups = sorted(dff["_group"].dropna().unique())

    for i, grp in enumerate(groups):
        gdf = dff[dff["_group"] == grp].sort_values("flight_date")
        color = TRACE_COLORS[i % len(TRACE_COLORS)]

        # Build hover fields safely
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
                f"<b>Emission/Seat:</b> %{{customdata[5]}} kg/hr<br>"
                f"<b>Ticket price:</b> %{{customdata[0]}}<br>"
                f"<b>Airline:</b> %{{customdata[1]}}<br>"
                f"<b>Aircraft:</b> %{{customdata[2]}}"
                "<extra></extra>"
            )
        ))

    # Title
    dest_part = dest if dest != "All" else "All Destinations"
    mode_label = {"avg": "AVG CO₂/hr", "est": "Est. CO₂/flight", "per_seat": "Emission/Seat"}.get(mode, mode)
    title = (
        f"{origin} → {dest_part}  |  "
        f"<span style='color:{accent}'>{mode_label}</span>  "
        f"|  grouped by {groupby.upper()}"
    )

    fig = _apply_theme(fig, title, y_label, accent)

    # ── Stats bar ─────────────────────────────────────────────────────
    stats_parts = []
    overall_mean   = dff[y_col].mean()
    overall_median = dff[y_col].median()
    overall_min    = dff[y_col].min()
    overall_max    = dff[y_col].max()

    stats_parts.append(
        html.Span([
            html.Span("FLEET STATS  //  ", style={"color": NEON_BLUE}),
            html.Span(f"MEAN: {overall_mean:,.0f}  ", style={"color": NEON_CYAN}),
            html.Span(f"MEDIAN: {overall_median:,.0f}  ", style={"color": NEON_PINK}),
            html.Span(f"MIN: {overall_min:,.0f}  ", style={"color": NEON_GREEN}),
            html.Span(f"MAX: {overall_max:,.0f}  ", style={"color": NEON_YELLOW}),
            html.Span(f"n={len(dff)}", style={"color": "#555"}),
            html.Span("    //    PER GROUP:  ", style={"color": NEON_BLUE}),
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
# 7. Chart helpers
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
            title=dict(text="FLIGHT DATE", font=dict(color=NEON_BLUE, size=11)),
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
# 8. Run
# =====================================================================
# Remove or comment out:
if __name__ == '__main__':
    app.run(debug=True)