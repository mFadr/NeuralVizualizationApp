"""
vizualizationGini.py
Dash vizualizace True Gini koeficientu pro PRICE — soustředěná na cenovou nerovnoměrnost.

Hlavní graf: Lorenzova křivka pro konkrétní trasu (origin → destination)
   ↳ kumulativní podíl populace × kumulativní podíl příjmu (cen)
   ↳ defaultní výběr: BER → AMS

Sekundární graf: Bar / Heatmap True Gini pro PRICE napříč všemi trasami

Vychází z: Santos & Dias (2024), Acta Scientiarum Technology, v.46, e64563
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from app_instance import app
from config import DATASET_PATHS

# =====================================================================
# 1. Cyberpunk téma
# =====================================================================
BG_COLOR       = "#0b0c10"
PANEL_BG       = "#1f2833"
NEON_CYAN      = "#66fcf1"
NEON_BLUE      = "#45a29e"
NEON_PINK      = "#ff007f"
NEON_YELLOW    = "#f5c518"
NEON_GREEN     = "#39ff14"
NEON_PURPLE    = "#9d4edd"
NEON_ORANGE    = "#ff6600"
TEXT_MUTED     = "#c5c6c7"
GRID_COLOR     = "#1e2a2a"
DROPDOWN_STYLE = {"color": "black"}

# Barvy pro Lorenzův graf
LORENZ_AREA_A   = "rgba(245,197,24,0.35)"   # oranžová s průhledností (Area A)
LORENZ_AREA_B   = "rgba(102,252,241,0.18)"  # cyan s průhledností (Area B)
LORENZ_CURVE    = NEON_CYAN
LORENZ_EQUALITY = NEON_PINK

# Konfigurace pouze pro PRICE
PRICE_CONFIG = {
    "id":      "price",
    "label":   "PRICE",
    "unit":    "USD",
    "col_key": "price",
    "accent":  NEON_CYAN,
    "desc":    "Ticket price inequality across flights"
}

LABEL_STYLE = {
    "color":         NEON_BLUE,
    "fontSize":      "10px",
    "letterSpacing": "1px",
    "marginBottom":  "4px",
    "display":       "block"
}
FILTER_CELL = {
    "display":       "inline-block",
    "verticalAlign": "top",
    "marginRight":   "20px"
}

# =====================================================================
# 2. Funkce Gini  (Santos & Dias 2024)
# =====================================================================
def true_gini(values: np.ndarray) -> float:
    """True Gini — rovnice 6, Santos & Dias (2024)."""
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
    """Mapuje hodnotu Gini na barvu podle velikosti."""
    if np.isnan(g):
        return "#333"
    if g >= 0.4:  return accent
    if g >= 0.25: return NEON_BLUE
    return "#2a4a4a"


def lorenz_points(values: np.ndarray):
    """
    Spočítá body Lorenzovy křivky.
    Vrací (x, y) — kumulativní podíly populace a hodnot (0–1).
    """
    v = values[~np.isnan(values)]
    v = v[v >= 0]
    n = len(v)
    if n < 2 or np.sum(v) == 0:
        return None, None
    sorted_v = np.sort(v)
    cum_v    = np.cumsum(sorted_v)
    x = np.concatenate([[0], np.arange(1, n + 1) / n])
    y = np.concatenate([[0], cum_v / cum_v[-1]])
    return x, y


# =====================================================================
# 3. Načítání dat a výpočet Gini
# =====================================================================
def find_col(df: pd.DataFrame, key: str):
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


# Cache cen na trasu pro rychlý lookup v Lorenz callback
ROUTE_PRICES = {}   # { (origin, destination): np.ndarray }


def compute_gini_table() -> pd.DataFrame:
    """
    Pro každou trasu (origin, destination) spočítá True Gini PRICE,
    průměr, medián, std, n.
    Současně naplní ROUTE_PRICES pro rychlý Lorenz lookup.
    """
    rows = []
    for origin, path in DATASET_PATHS.items():
        try:
            df = pd.read_csv(path, sep=r"[\t;,]", engine="python")
            df.columns = df.columns.str.strip().str.lower()
        except Exception as e:
            print(f"  ✗ {origin}: {e}")
            continue

        dest_col  = find_col(df, "destination")
        price_col = find_col(df, "price")
        if dest_col is None or price_col is None:
            continue

        destinations = sorted(df[dest_col].dropna().astype(str).str.upper().unique())

        for dest in destinations:
            sub = df[df[dest_col].astype(str).str.upper() == dest]
            if sub.empty:
                continue

            vals = parse_numeric(sub[price_col])
            valid = vals[~np.isnan(vals)]
            valid = valid[valid >= 0]
            n = len(valid)
            if n < 2:
                continue

            # Cache pro Lorenzovu křivku
            ROUTE_PRICES[(origin, dest)] = valid

            gt = true_gini(vals)
            rows.append({
                "origin":         origin,
                "destination":    dest,
                "n":              n,
                "true_gini":      round(gt, 6) if not np.isnan(gt) else None,
                "mean":           round(float(np.mean(valid)), 4),
                "median":         round(float(np.median(valid)), 4),
                "std":            round(float(np.std(valid)), 4),
                "interpretation": interpret_gini(gt),
            })

    return pd.DataFrame(rows)


print("Computing Gini coefficients (PRICE only)...")
GINI_TABLE = compute_gini_table()
print(f"✓ Gini table ready — {len(GINI_TABLE)} rows  ·  "
      f"{len(ROUTE_PRICES)} routes cached for Lorenz\n")

ALL_ORIGINS      = sorted(GINI_TABLE["origin"].unique())      if not GINI_TABLE.empty else []
ALL_DESTINATIONS = sorted(GINI_TABLE["destination"].unique()) if not GINI_TABLE.empty else []

# Defaultní výběr pro Lorenzův graf
DEFAULT_LORENZ_ORIGIN = "BER" if "BER" in ALL_ORIGINS      else (ALL_ORIGINS[0]      if ALL_ORIGINS      else None)
DEFAULT_LORENZ_DEST   = "AMS" if "AMS" in ALL_DESTINATIONS else (ALL_DESTINATIONS[0] if ALL_DESTINATIONS else None)

# =====================================================================
# 4. Rozložení
# =====================================================================
layout = html.Div([

    # ── Tlačítko zpět ──────────────────────────────────────────────────
    html.A(
        "← BACK TO MAIN",
        href="/",
        style={
            "display":         "inline-block",
            "color":           NEON_CYAN,
            "border":          f"1px solid {NEON_BLUE}",
            "padding":         "6px 16px",
            "borderRadius":    "6px",
            "textDecoration":  "none",
            "fontSize":        "11px",
            "letterSpacing":   "2px",
            "marginBottom":    "14px",
            "fontFamily":      "Courier New, monospace",
            "backgroundColor": PANEL_BG
        }
    ),

    # ── Titulek ────────────────────────────────────────────────────────
    html.Div([
        html.H2(
            "◈  GINI INEQUALITY ANALYZER  ·  PRICE",
            style={
                "color":         NEON_CYAN,
                "textShadow":    f"0 0 16px {NEON_CYAN}",
                "letterSpacing": "4px",
                "fontSize":      "18px",
                "fontFamily":    "Courier New, monospace",
                "margin":        "0 0 4px 0",
                "textAlign":     "center"
            }
        ),
        html.Div(
            "TRUE GINI COEFFICIENT  ·  Santos & Dias (2024)  ·  Lorenz Curve & Distribution",
            style={
                "color":         NEON_BLUE,
                "fontSize":      "10px",
                "letterSpacing": "2px",
                "fontFamily":    "Courier New, monospace",
                "textAlign":     "center",
                "marginBottom":  "16px"
            }
        )
    ]),

    # ──────────────────────────────────────────────────────────────────
    # CHART #1 — LORENZ CURVE  (s vlastní lištou Origin/Destination)
    # ──────────────────────────────────────────────────────────────────
    html.Div([

        # Lišta filtrů pro Lorenz
        html.Div([
            html.Span("◈  LORENZ CURVE  ·  ROUTE-SPECIFIC INEQUALITY", style={
                "color":         NEON_CYAN,
                "fontSize":      "11px",
                "letterSpacing": "2px",
                "fontWeight":    "bold",
                "marginRight":   "24px",
                "fontFamily":    "Courier New, monospace"
            }),

            html.Div([
                html.Label("ORIGIN", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="lorenz-origin",
                    options=[{"label": o, "value": o} for o in ALL_ORIGINS],
                    value=DEFAULT_LORENZ_ORIGIN,
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "120px"}
                )
            ], style=FILTER_CELL),

            html.Div([
                html.Label("DESTINATION", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="lorenz-dest",
                    options=[{"label": d, "value": d} for d in ALL_DESTINATIONS],
                    value=DEFAULT_LORENZ_DEST,
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "140px"}
                )
            ], style=FILTER_CELL),

        ], style={
            "backgroundColor": PANEL_BG,
            "padding":         "10px 18px",
            "borderRadius":    "10px 10px 0 0",
            "borderBottom":    f"1px solid {NEON_CYAN}30",
            "display":         "flex",
            "alignItems":      "center",
            "flexWrap":        "wrap"
        }),

        # Samotný Lorenzův graf
        html.Div([
            dcc.Graph(
                id="lorenz-chart",
                config={"displayModeBar": False, "responsive": True},
                style={"height": "440px"}
            )
        ], style={
            "borderRadius":    "0 0 12px 12px",
            "backgroundColor": PANEL_BG
        })

    ], style={
        "borderRadius": "12px",
        "boxShadow":    f"0 0 18px {NEON_CYAN}30",
        "border":       f"1px solid {NEON_CYAN}20",
        "marginBottom": "16px"
    }),

    # ──────────────────────────────────────────────────────────────────
    # CHART #2 — Bar / Heatmap pro PRICE napříč všemi trasami
    # ──────────────────────────────────────────────────────────────────
    html.Div([

        # Lišta filtrů pro chart #2
        html.Div([

            html.Span("◈  PRICE GINI  ·  ALL ROUTES", style={
                "color":         NEON_PURPLE,
                "fontSize":      "11px",
                "letterSpacing": "2px",
                "fontWeight":    "bold",
                "marginRight":   "24px",
                "fontFamily":    "Courier New, monospace"
            }),

            html.Div([
                html.Label("ORIGIN", style=LABEL_STYLE),
                dcc.Dropdown(
                    id="gini-origin",
                    options=[{"label": "All Origins", "value": "ALL"}] +
                            [{"label": o, "value": o} for o in ALL_ORIGINS],
                    value="ALL",
                    clearable=False,
                    style={**DROPDOWN_STYLE, "width": "150px"}
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
                    style={**DROPDOWN_STYLE, "width": "180px"}
                )
            ], style=FILTER_CELL),

            # Oddělovač
            html.Span(style={
                "display":         "inline-block",
                "width":           "1px",
                "height":          "44px",
                "backgroundColor": NEON_BLUE,
                "verticalAlign":   "middle",
                "opacity":         "0.4",
                "marginRight":     "20px"
            }),

            # Režim grafu
            html.Div([
                html.Label("CHART MODE", style=LABEL_STYLE),
                dcc.RadioItems(
                    id="gini-chart-mode",
                    options=[
                        {"label": "  Bar",     "value": "bar"},
                        {"label": "  Heatmap", "value": "heatmap"},
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
            "padding":         "10px 18px",
            "borderRadius":    "10px 10px 0 0",
            "borderBottom":    f"1px solid {NEON_PURPLE}30",
            "display":         "block",
            "alignItems":      "center",
            "flexWrap":        "wrap"
        }),

        # Samotný graf
        html.Div([
            dcc.Graph(
                id="gini-chart-price",
                config={"displayModeBar": False, "responsive": True},
                style={"height": "420px"}
            )
        ], style={
            "borderRadius":    "0 0 12px 12px",
            "backgroundColor": PANEL_BG
        })

    ], style={
        "borderRadius": "12px",
        "boxShadow":    f"0 0 18px {NEON_PURPLE}30",
        "border":       f"1px solid {NEON_PURPLE}20"
    })

], style={
    "backgroundColor": BG_COLOR,
    "color":           NEON_CYAN,
    "padding":         "14px 22px",
    "fontFamily":      "Courier New, monospace",
    "boxSizing":       "border-box",
    "minHeight":       "100vh"
})


# =====================================================================
# 5. Pomocná funkce — aplikace tématu na figure
# =====================================================================
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
        margin=dict(l=55, r=30, t=45, b=45),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#333",
                    font=dict(size=10)),
        hovermode="closest"
    )
    return fig


# =====================================================================
# 5a. LORENZOVA KŘIVKA — callback
# =====================================================================
@app.callback(
    Output("lorenz-chart", "figure"),
    Input("lorenz-origin", "value"),
    Input("lorenz-dest",   "value"),
)
def update_lorenz(origin, dest):
    fig = go.Figure()

    if origin is None or dest is None:
        fig.add_annotation(
            text="SELECT ORIGIN AND DESTINATION",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, "LORENZ CURVE", NEON_CYAN)

    values = ROUTE_PRICES.get((origin, dest))
    if values is None or len(values) < 2:
        fig.add_annotation(
            text=f"NO DATA FOR {origin} → {dest}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, f"LORENZ CURVE  ·  {origin} → {dest}", NEON_CYAN)

    x_lc, y_lc = lorenz_points(values)
    if x_lc is None:
        fig.add_annotation(
            text=f"INSUFFICIENT DATA FOR {origin} → {dest}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, f"LORENZ CURVE  ·  {origin} → {dest}", NEON_CYAN)

    g_value = true_gini(values)
    g_text  = f"{g_value:.4f}" if not np.isnan(g_value) else "N/A"
    g_label = interpret_gini(g_value)

    # Trace 1: Area B — pod Lorenzovou křivkou (cyan tlumená výplň)
    fig.add_trace(go.Scatter(
        x=x_lc, y=y_lc,
        mode="lines",
        name="Area B  (under Lorenz curve)",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="tozeroy",
        fillcolor=LORENZ_AREA_B,
        hoverinfo="skip",
        showlegend=True
    ))

    # Trace 2: Lorenzova křivka  + Area A jako fill 'tonexty' k linii rovnosti.
    # Plotly: fill='tonexty' vyplní oblast mezi tímto trace a předchozím trace.
    # Aby Area A byla mezi Lorenz křivkou a linií rovnosti, musíme nejprve
    # přidat Lorenz, pak linii rovnosti s fill='tonexty'.
    fig.add_trace(go.Scatter(
        x=x_lc, y=y_lc,
        mode="lines",
        name=f"Lorenz Curve  (Gini = {g_text})",
        line=dict(color=LORENZ_CURVE, width=3),
        hovertemplate=(
            "<b>Cumulative population:</b> %{x:.2%}<br>"
            "<b>Cumulative price share:</b> %{y:.2%}"
            "<extra></extra>"
        )
    ))

    # Trace 3: Line of Equality — vyplní Area A směrem k Lorenz křivce (předchozí trace)
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines",
        name="Line of Equality",
        line=dict(color=LORENZ_EQUALITY, width=2, dash="dash"),
        fill="tonexty",
        fillcolor=LORENZ_AREA_A,
        hovertemplate="Perfect equality<br>x=%{x:.2f}, y=%{y:.2f}<extra></extra>"
    ))

    # Anotace s metadaty v levém horním rohu
    n_obs    = len(values)
    mean_v   = float(np.mean(values))
    median_v = float(np.median(values))

    info_text = (
        f"<b>Route:</b> {origin} → {dest}<br>"
        f"<b>True Gini:</b> {g_text}  ({g_label})<br>"
        f"<b>n:</b> {n_obs:,}  ·  "
        f"<b>mean:</b> ${mean_v:.2f}  ·  "
        f"<b>median:</b> ${median_v:.2f}"
    )
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.98, xanchor="left", yanchor="top",
        text=info_text,
        showarrow=False,
        font=dict(color=TEXT_MUTED, size=10, family="Courier New, monospace"),
        bgcolor="rgba(11,12,16,0.85)",
        bordercolor=NEON_CYAN,
        borderwidth=1,
        borderpad=8,
        align="left"
    )

    fig.update_xaxes(
        range=[0, 1],
        title="Cumulative Share of Population (flights, sorted by price)",
        tickformat=".0%"
    )
    fig.update_yaxes(
        range=[0, 1],
        title="Cumulative Share of Price",
        tickformat=".0%"
    )

    title = f"LORENZ CURVE  ·  {origin} → {dest}  ·  Gini = {g_text}  ({g_label})"
    return _apply_theme(fig, title, NEON_CYAN)


# =====================================================================
# 5b. PRICE GINI — Bar / Heatmap callback
# =====================================================================
def _filter_table(origin: str, dest: str) -> pd.DataFrame:
    df = GINI_TABLE.copy()
    if origin != "ALL":
        df = df[df["origin"] == origin]
    if dest != "ALL":
        df = df[df["destination"] == dest]
    return df


def _build_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="NO DATA", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, PRICE_CONFIG["label"], PRICE_CONFIG["accent"])

    df = df.copy()
    df["route"] = df["origin"] + " → " + df["destination"]
    df = df.sort_values("true_gini", ascending=True)

    bar_colors = [gini_color(g, PRICE_CONFIG["accent"]) for g in df["true_gini"]]

    fig = go.Figure(go.Bar(
        x=df["true_gini"],
        y=df["route"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(color=BG_COLOR, width=0.5)),
        customdata=df[["mean", "median", "std", "n", "interpretation"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "<b>True Gini:</b> %{x:.4f}<br>"
            "<b>Mean:</b> $%{customdata[0]:.2f}<br>"
            "<b>Median:</b> $%{customdata[1]:.2f}<br>"
            "<b>Std:</b> %{customdata[2]:.2f}<br>"
            "<b>n:</b> %{customdata[3]}<br>"
            "<b>Inequality:</b> %{customdata[4]}"
            "<extra></extra>"
        ),
        text=df["true_gini"].apply(lambda v: f"{v:.3f}" if pd.notna(v) else ""),
        textposition="outside",
        textfont=dict(color=TEXT_MUTED, size=9)
    ))

    # Referenční čáry
    for val, label, color in [
        (0.2, "Low",      "#2a5a48"),
        (0.3, "Moderate", "#5a5a20"),
        (0.4, "High",     "#7a2a20"),
    ]:
        fig.add_vline(
            x=val, line_dash="dot", line_color=color, line_width=1,
            annotation_text=label,
            annotation_font=dict(color=color, size=8),
            annotation_position="top"
        )

    fig.update_xaxes(
        range=[0, min(df["true_gini"].max() * 1.3, 1.0)
        if not df.empty else 1.0]
    )

    title = "PRICE  ·  TRUE GINI  (0 = equality, 1 = max inequality)"
    return _apply_theme(fig, title, PRICE_CONFIG["accent"])


def _build_heatmap(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="NO DATA", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=NEON_PINK, size=14)
        )
        return _apply_theme(fig, PRICE_CONFIG["label"], PRICE_CONFIG["accent"])

    pivot = df.pivot_table(
        index="origin", columns="destination",
        values="true_gini", aggfunc="mean"
    )

    colorscale = [
        [0.0,  "#0b0c10"],
        [0.25, "#1f2833"],
        [0.5,  NEON_BLUE],
        [0.75, PRICE_CONFIG["accent"]],
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

    title = "PRICE  ·  HEATMAP  (origin × destination)"
    return _apply_theme(fig, title, PRICE_CONFIG["accent"])


@app.callback(
    Output("gini-chart-price", "figure"),
    Input("gini-origin",     "value"),
    Input("gini-dest",       "value"),
    Input("gini-chart-mode", "value"),
)
def update_price_chart(origin, dest, chart_mode):
    df = _filter_table(origin, dest)
    if chart_mode == "heatmap":
        return _build_heatmap(df)
    return _build_bar(df)


# =====================================================================
# 6. Vstupní bod (jen pro lokální vývoj)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8055))
    app.run(host="0.0.0.0", port=port, debug=False)
