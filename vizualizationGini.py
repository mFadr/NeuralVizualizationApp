"""
vizualizationGini.py
Dash visualization of True Gini coefficients per route.
4 charts: Price · Est. CO2 · AVG CO2 · Emission/Seat
Filters: Origin · Destination
Based on: Santos & Dias (2024), Acta Scientiarum Technology, v.46, e64563
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from app_instance import app
from config import DATASET_PATHS

# =====================================================================
# 1. Cyberpunk Theme
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

# One accent colour per chart metric
CHART_CONFIG = [
    {
        "id":      "price",
        "label":   "PRICE",
        "unit":    "USD",
        "col_key": "price",
        "accent":  NEON_CYAN,
        "desc":    "Ticket price inequality across flights"
    },
    {
        "id":      "est_co2",
        "label":   "EST. CO₂  (kg/flight)",
        "unit":    "kg",
        "col_key": "est. co2 (kg)",
        "accent":  NEON_GREEN,
        "desc":    "Total estimated CO₂ per flight inequality"
    },
    {
        "id":      "avg_co2",
        "label":   "AVG CO₂  (kg/hr)",
        "unit":    "kg/hr",
        "col_key": "avg co2 (kg/hr)",
        "accent":  NEON_PINK,
        "desc":    "Average hourly CO₂ emission inequality"
    },
    {
        "id":      "emission_seat",
        "label":   "EMISSION / SEAT  (kg/hr)",
        "unit":    "kg/hr/seat",
        "col_key": "emissions_per_seat (avg)",
        "accent":  NEON_YELLOW,
        "desc":    "Per-seat emission inequality"
    },
]

LABEL_STYLE = {
    "color":         NEON_BLUE,
    "fontSize":      "10px",
    "letterSpacing": "1px",
    "marginBottom":  "4px",
    "display":       "block"
}
FILTER_CELL = {
    "display":      "inline-block",
    "verticalAlign": "top",
    "marginRight":  "20px"
}

# =====================================================================
# 2. Gini functions  (Santos & Dias 2024)
# =====================================================================
def true_gini(values: np.ndarray) -> float:
    """True Gini — Eq. 6, Santos & Dias (2024)."""
    v = values[~np.isnan(values)]
    v = v[v >= 0]
    n = len(v)
    if n < 2 or np.mean(v) == 0:
        return np.nan
    diff_sum = np.sum(np.abs(v[:, None] - v[None, :])) / 2
    return diff_sum / (np.mean(v) * n * (n - 1))


def interpret_gini(g: float) -> str:
    if np.isnan(g):       return "N/A"
    if g < 0.2:           return "Very low"
    if g < 0.3:           return "Low"
    if g < 0.4:           return "Moderate"
    if g < 0.5:           return "High"
    return                       "Very high"


def gini_color(g: float, accent: str) -> str:
    """Map Gini value to a colour gradient from dim → accent."""
    if np.isnan(g):
        return "#333"
    # blend from dark grey to the accent colour based on magnitude
    t = min(g / 0.6, 1.0)
    # simple: return accent at full saturation above 0.4, dim below
    if g >= 0.4:
        return accent
    if g >= 0.25:
        return NEON_BLUE
    return "#2a4a4a"

# =====================================================================
# 3. Data loading & Gini computation
# =====================================================================
def find_col(df: pd.DataFrame, key: str):
    """Fuzzy column finder — strips spaces, dots, brackets."""
    def clean(s):
        return s.lower().replace(" ","").replace(".","").replace("(","").replace(")","")
    key_c = clean(key)
    for col in df.columns:
        if key_c in clean(col) or clean(col) in key_c:
            return col
    return None


def parse_numeric(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors="coerce"
    ).values


def compute_gini_table() -> pd.DataFrame:
    """
    For every (origin, destination, metric) compute True Gini,
    mean, median, std, n.
    Returns a tidy DataFrame with one row per combination.
    """
    rows = []
    for origin, path in DATASET_PATHS.items():
        try:
            df = pd.read_csv(path, sep=r"[\t;,]", engine="python")
            df.columns = df.columns.str.strip().str.lower()
        except Exception as e:
            print(f"  ✗ {origin}: {e}")
            continue

        dest_col = find_col(df, "destination")
        if dest_col is None:
            print(f"  ✗ {origin}: no destination column")
            continue

        destinations = sorted(df[dest_col].dropna().astype(str).str.upper().unique())

        for dest in destinations:
            sub = df[df[dest_col].astype(str).str.upper() == dest]
            if sub.empty:
                continue

            for cfg in CHART_CONFIG:
                col = find_col(sub, cfg["col_key"])
                if col is None:
                    continue
                vals = parse_numeric(sub[col])
                valid = vals[~np.isnan(vals)]
                valid = valid[valid >= 0]
                n = len(valid)
                if n < 2:
                    continue

                gt = true_gini(vals)
                rows.append({
                    "origin":          origin,
                    "destination":     dest,
                    "metric":          cfg["id"],
                    "metric_label":    cfg["label"],
                    "n":               n,
                    "true_gini":       round(gt, 6) if not np.isnan(gt) else None,
                    "mean":            round(float(np.mean(valid)), 4),
                    "median":          round(float(np.median(valid)), 4),
                    "std":             round(float(np.std(valid)), 4),
                    "interpretation":  interpret_gini(gt),
                })

    return pd.DataFrame(rows)


print("Computing Gini coefficients...")
GINI_TABLE = compute_gini_table()
print(f"✓ Gini table ready — {len(GINI_TABLE)} rows\n")

ALL_ORIGINS      = sorted(GINI_TABLE["origin"].unique())      if not GINI_TABLE.empty else []
ALL_DESTINATIONS = sorted(GINI_TABLE["destination"].unique()) if not GINI_TABLE.empty else []

# =====================================================================
# 4. Layout
# =====================================================================
layout = html.Div([

    # ── Back button ───────────────────────────────────────────────────
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

    # ── Title ─────────────────────────────────────────────────────────
    html.Div([
        html.H2(
            "◈  GINI INEQUALITY ANALYZER",
            style={
                "color":      NEON_CYAN,
                "textShadow": f"0 0 16px {NEON_CYAN}",
                "letterSpacing": "4px",
                "fontSize":   "18px",
                "fontFamily": "Courier New, monospace",
                "margin":     "0 0 4px 0",
                "textAlign":  "center"
            }
        ),
        html.Div(
            "TRUE GINI COEFFICIENT  ·  Santos & Dias (2024)  ·  "
            "Price  ·  CO₂  ·  Emission/Seat",
            style={
                "color":      NEON_BLUE,
                "fontSize":   "10px",
                "letterSpacing": "2px",
                "fontFamily": "Courier New, monospace",
                "textAlign":  "center",
                "marginBottom": "16px"
            }
        )
    ]),

    # ── Filter bar ────────────────────────────────────────────────────
    html.Div([

        html.Div([
            html.Label("ORIGIN", style=LABEL_STYLE),
            dcc.Dropdown(
                id="gini-origin",
                options=[{"label": "All Origins", "value": "ALL"}] +
                        [{"label": o, "value": o} for o in ALL_ORIGINS],
                value="ALL",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "160px"}
            )
        ], style=FILTER_CELL),

        html.Div([
            html.Label("DESTINATION", style=LABEL_STYLE),
            dcc.Dropdown(
                id="gini-dest",
                options=[{"label": "All Destinations", "value": "ALL"}] +
                        [{"label": d, "value": d} for d in ALL_DESTINATIONS],
                value="ALL",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "190px"}
            )
        ], style=FILTER_CELL),

        # Divider
        html.Span(style={
            "display":         "inline-block",
            "width":           "1px",
            "height":          "44px",
            "backgroundColor": NEON_BLUE,
            "verticalAlign":   "middle",
            "opacity":         "0.4",
            "marginRight":     "20px"
        }),

        # Gini type selector
        html.Div([
            html.Label("GINI TYPE", style=LABEL_STYLE),
            dcc.RadioItems(
                id="gini-type",
                options=[
                    {"label": "  True Gini  (recommended)", "value": "true_gini"},
                ],
                value="true_gini",
                labelStyle={
                    "display":     "inline-block",
                    "color":       TEXT_MUTED,
                    "marginRight": "14px",
                    "fontSize":    "12px"
                }
            )
        ], style=FILTER_CELL),

        # Chart mode
        html.Div([
            html.Label("CHART MODE", style=LABEL_STYLE),
            dcc.RadioItems(
                id="gini-chart-mode",
                options=[
                    {"label": "  Bar",      "value": "bar"},
                    {"label": "  Heatmap",  "value": "heatmap"},
                ],
                value="bar",
                labelStyle={
                    "display":     "inline-block",
                    "color":       TEXT_MUTED,
                    "marginRight": "14px",
                    "fontSize":    "12px"
                }
            )
        ], style=FILTER_CELL),

    ], style={
        "backgroundColor": PANEL_BG,
        "padding":         "12px 20px",
        "borderRadius":    "12px",
        "marginBottom":    "14px",
        "boxShadow":       f"0 0 16px {NEON_BLUE}50",
        "border":          f"1px solid {NEON_BLUE}20",
        "display":         "flex",
        "alignItems":      "center",
        "flexWrap":        "wrap"
    }),

    # ── Stats summary bar ─────────────────────────────────────────────
    html.Div(id="gini-stats-bar", style={
        "backgroundColor": PANEL_BG,
        "padding":         "8px 20px",
        "borderRadius":    "10px",
        "marginBottom":    "14px",
        "fontSize":        "11px",
        "color":           TEXT_MUTED,
        "border":          f"1px solid {NEON_BLUE}20",
        "fontFamily":      "Courier New, monospace",
        "overflowX":       "auto",
        "whiteSpace":      "nowrap"
    }),

    # ── 4 charts in 2×2 grid ─────────────────────────────────────────
    html.Div([
        html.Div([
            dcc.Graph(
                id=f"gini-chart-{cfg['id']}",
                config={"displayModeBar": False, "responsive": True},
                style={"height": "100%"}
            )
        ], style={
            "borderRadius":  "12px",
            "overflow":      "hidden",
            "boxShadow":     f"0 0 16px {cfg['accent']}30",
            "border":        f"1px solid {cfg['accent']}20",
            "backgroundColor": PANEL_BG
        })
        for cfg in CHART_CONFIG
    ], style={
        "display":             "grid",
        "gridTemplateColumns": "1fr 1fr",
        "gridTemplateRows":    "1fr 1fr",
        "gap":                 "16px",
        "flex":                "1",
        "minHeight":           "0"
    })

], style={
    "backgroundColor": BG_COLOR,
    "color":           NEON_CYAN,
    "padding":         "14px 22px",
    "fontFamily":      "Courier New, monospace",
    "boxSizing":       "border-box",
    "display":         "flex",
    "flexDirection":   "column",
    "height":          "100vh",
    "overflow":        "hidden"
})

# =====================================================================
# 5. Callbacks
# =====================================================================
def _filter_table(origin: str, dest: str) -> pd.DataFrame:
    df = GINI_TABLE.copy()
    if origin != "ALL":
        df = df[df["origin"] == origin]
    if dest != "ALL":
        df = df[df["destination"] == dest]
    return df


def _apply_theme(fig, title: str, accent: str) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color=accent, size=12, family="Courier New, monospace")
        ),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Courier New, monospace", size=11),
        margin=dict(l=50, r=30, t=45, b=40),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#333", font=dict(size=10)),
        hovermode="closest"
    )
    return fig


def _build_bar(df_metric: pd.DataFrame, cfg: dict) -> go.Figure:
    """Grouped bar chart — one bar per origin/dest combination."""
    if df_metric.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="NO DATA", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, cfg["label"], cfg["accent"])

    # Create route label
    df_metric = df_metric.copy()
    df_metric["route"] = df_metric["origin"] + " → " + df_metric["destination"]
    df_metric = df_metric.sort_values("true_gini", ascending=True)

    # Colour bars by Gini magnitude
    bar_colors = [gini_color(g, cfg["accent"])
                  for g in df_metric["true_gini"]]

    fig = go.Figure(go.Bar(
        x=df_metric["true_gini"],
        y=df_metric["route"],
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color=BG_COLOR, width=0.5)
        ),
        customdata=df_metric[["mean", "median", "std", "n", "interpretation"]].values,
        hovertemplate=(
                "<b>%{y}</b><br>"
                f"<b>True Gini:</b> %{{x:.4f}}<br>"
                "<b>Mean:</b> %{customdata[0]:.2f} " + cfg["unit"] + "<br>"
                                                                     "<b>Median:</b> %{customdata[1]:.2f} " + cfg["unit"] + "<br>"
                                                                                                                            "<b>Std:</b> %{customdata[2]:.2f}<br>"
                                                                                                                            "<b>n:</b> %{customdata[3]}<br>"
                                                                                                                            "<b>Inequality:</b> %{customdata[4]}"
                                                                                                                            "<extra></extra>"
        ),
        text=df_metric["true_gini"].apply(lambda v: f"{v:.3f}" if pd.notna(v) else ""),
        textposition="outside",
        textfont=dict(color=TEXT_MUTED, size=9)
    ))

    # Reference lines
    for val, label, color in [
        (0.2, "Low", "#2a5a48"),
        (0.3, "Moderate", "#5a5a20"),
        (0.4, "High", "#7a2a20"),
    ]:
        fig.add_vline(
            x=val, line_dash="dot", line_color=color, line_width=1,
            annotation_text=label,
            annotation_font=dict(color=color, size=8),
            annotation_position="top"
        )

    fig.update_xaxes(range=[0, min(df_metric["true_gini"].max() * 1.3, 1.0)
    if not df_metric.empty else 1.0])

    title = f"{cfg['label']}  ·  TRUE GINI  (0 = equality, 1 = max inequality)"
    return _apply_theme(fig, title, cfg["accent"])


def _build_heatmap(df_metric: pd.DataFrame, cfg: dict) -> go.Figure:
    """Heatmap — rows = origins, cols = destinations."""
    if df_metric.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="NO DATA", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, cfg["label"], cfg["accent"])

    pivot = df_metric.pivot_table(
        index="origin", columns="destination",
        values="true_gini", aggfunc="mean"
    )

    # Custom colorscale from dark → accent
    colorscale = [
        [0.0,  "#0b0c10"],
        [0.25, "#1f2833"],
        [0.5,  NEON_BLUE],
        [0.75, cfg["accent"]],
        [1.0,  "#ffffff"]
    ]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=colorscale,
        zmin=0, zmax=0.6,
        text=[[f"{v:.3f}" if not np.isnan(v) else "N/A"
               for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, color="white"),
        hovertemplate=(
            "<b>%{y} → %{x}</b><br>"
            "<b>True Gini:</b> %{z:.4f}"
            "<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="Gini", font=dict(color=TEXT_MUTED, size=10)),
            tickfont=dict(color=TEXT_MUTED, size=9),
            len=0.8
        )
    ))

    title = f"{cfg['label']}  ·  HEATMAP  (origin × destination)"
    return _apply_theme(fig, title, cfg["accent"])


# Register one callback per chart
for _cfg in CHART_CONFIG:
    _metric_id = _cfg["id"]

    @app.callback(
        Output(f"gini-chart-{_metric_id}", "figure"),
        Input("gini-origin",     "value"),
        Input("gini-dest",       "value"),
        Input("gini-chart-mode", "value"),
    )
    def _update_chart(origin, dest, chart_mode, metric_id=_metric_id):
        cfg_match = next(c for c in CHART_CONFIG if c["id"] == metric_id)
        df_filtered = _filter_table(origin, dest)
        df_metric   = df_filtered[df_filtered["metric"] == metric_id]

        if chart_mode == "heatmap":
            return _build_heatmap(df_metric, cfg_match)
        return _build_bar(df_metric, cfg_match)


# Stats summary bar
@app.callback(
    Output("gini-stats-bar", "children"),
    Input("gini-origin", "value"),
    Input("gini-dest",   "value"),
)
def update_stats(origin, dest):
    df = _filter_table(origin, dest)
    if df.empty:
        return "No data available."

    items = []
    for cfg in CHART_CONFIG:
        sub = df[df["metric"] == cfg["id"]]
        if sub.empty:
            continue
        mean_g  = sub["true_gini"].mean()
        min_g   = sub["true_gini"].min()
        max_g   = sub["true_gini"].max()
        min_r   = sub.loc[sub["true_gini"].idxmin(), "origin"] + "→" + \
                  sub.loc[sub["true_gini"].idxmin(), "destination"] \
            if not sub.empty else "—"
        max_r   = sub.loc[sub["true_gini"].idxmax(), "origin"] + "→" + \
                  sub.loc[sub["true_gini"].idxmax(), "destination"] \
            if not sub.empty else "—"

        items.append(html.Span([
            html.Span(cfg["label"] + "  ",
                      style={"color": cfg["accent"], "fontWeight": "bold"}),
            html.Span(f"avg={mean_g:.3f}  ",
                      style={"color": TEXT_MUTED}),
            html.Span(f"min={min_g:.3f} ({min_r})  ",
                      style={"color": NEON_GREEN}),
            html.Span(f"max={max_g:.3f} ({max_r})  ",
                      style={"color": NEON_PINK}),
            html.Span("  |  ", style={"color": "#333"}),
        ]))

    return items if items else "No statistics available."


# =====================================================================
# 6. Entry point (local dev only)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8055))
    app.run(host="0.0.0.0", port=port, debug=False)