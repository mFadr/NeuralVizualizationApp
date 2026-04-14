import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# =====================================================================
# 1. Configuration
# =====================================================================

from config import DATASET_PATHS

sources_cities = ["PRG", "WAW", "BER", "VIE", "BUD"]
targets_cities = ["FCO", "BCN", "LHR", "AMS"]

# =====================================================================
# 2. Cyberpunk Theme
# =====================================================================
BG_COLOR    = "#0b0c10"
PANEL_BG    = "#1f2833"
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_YELLOW = "#f5c518"
TEXT_MUTED  = "#c5c6c7"

# Node colours: sources = cyan family, targets = pink family
SOURCE_COLORS = ["#66fcf1", "#45a29e", "#00b4d8", "#0077b6", "#023e8a"]
TARGET_COLORS = ["#ff007f", "#c9184a", "#ff4d6d", "#ff758f"]

# Link colours per stat method (semi-transparent)
LINK_COLOR_MEAN   = "rgba(102,252,241,0.25)"   # cyan tint
LINK_COLOR_MEDIAN = "rgba(255,0,127,0.25)"      # pink tint

DROPDOWN_STYLE = {"color": "black"}
LABEL_STYLE = {
    "color": NEON_BLUE, "fontSize": "10px",
    "letterSpacing": "1px", "marginBottom": "4px", "display": "block"
}
FILTER_CELL = {"display": "inline-block", "verticalAlign": "top", "marginRight": "20px"}

# =====================================================================
# 3. Load & compute per-route statistics from real CSV files
# =====================================================================
def load_form_csv(path):
    """Load a _form.csv and return cleaned DataFrame."""
    df = pd.read_csv(path, sep=r"[\t;,]", engine="python")
    df.columns = df.columns.str.strip().str.lower()

    # Normalise destination column name
    for col in ["destination", "dest"]:
        if col in df.columns:
            df.rename(columns={col: "destination"}, inplace=True)
            break

    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True),
        errors="coerce"
    )
    df = df.dropna(subset=["price", "destination"])
    df["destination"] = df["destination"].astype(str).str.strip().str.upper()
    return df


def compute_route_stats(dataset_paths, sources, targets):
    """
    For every (origin, destination) pair compute mean and median
    from the real scraped price records.

    Returns two dicts keyed by (origin, destination):
        route_mean   → float
        route_median → float
    Also returns the raw per-route price Series for diagnostics.
    """
    route_mean   = {}
    route_median = {}
    route_counts = {}

    for origin, path in dataset_paths.items():
        if origin not in sources:
            continue
        try:
            df = load_form_csv(path)
        except Exception as e:
            print(f"✗ Could not load {origin} from {path}: {e}")
            # Fill with NaN so the diagram still renders
            for dest in targets:
                route_mean[(origin, dest)]   = np.nan
                route_median[(origin, dest)] = np.nan
                route_counts[(origin, dest)] = 0
            continue

        for dest in targets:
            prices = df.loc[df["destination"] == dest, "price"].dropna()
            n = len(prices)
            route_counts[(origin, dest)] = n
            if n > 0:
                route_mean[(origin, dest)]   = float(prices.mean())
                route_median[(origin, dest)] = float(prices.median())
            else:
                route_mean[(origin, dest)]   = np.nan
                route_median[(origin, dest)] = np.nan
            print(
                f"  {origin}→{dest}: n={n:>5}  "
                f"mean=${route_mean[(origin,dest)]:.2f}  "
                f"median=${route_median[(origin,dest)]:.2f}"
                if n > 0 else
                f"  {origin}→{dest}: NO DATA"
            )

    return route_mean, route_median, route_counts


print("Computing route statistics from real data...")
route_mean, route_median, route_counts = compute_route_stats(
    DATASET_PATHS, sources_cities, targets_cities
)
print("Done.\n")

# =====================================================================
# 4. Build price tables from computed stats
#    Layout: price_table[dest_idx][src_idx]  (same as original)
# =====================================================================
def build_price_table(stat_dict, sources, targets):
    """Convert route stat dict → 2-D list [dest][source]."""
    table = []
    for dest in targets:
        row = []
        for src in sources:
            val = stat_dict.get((src, dest), np.nan)
            row.append(val if not np.isnan(val) else 0.0)  # 0 = invisible link
        table.append(row)
    return table


mean_table   = build_price_table(route_mean,   sources_cities, targets_cities)
median_table = build_price_table(route_median, sources_cities, targets_cities)

# =====================================================================
# 5. Sankey link builder
# =====================================================================
nodes        = sources_cities + targets_cities
city_to_idx  = {city: i for i, city in enumerate(nodes)}
node_colors  = SOURCE_COLORS + TARGET_COLORS


def build_links(selected_sources, price_tbl, link_color):
    """Build Sankey link arrays filtered to selected source cities."""
    sources_out, targets_out, values_out, labels_out, colors_out = [], [], [], [], []

    for i, src in enumerate(sources_cities):
        if src not in selected_sources:
            continue
        for j, dest in enumerate(targets_cities):
            val = price_tbl[j][i]
            if val <= 0:
                continue
            sources_out.append(city_to_idx[src])
            targets_out.append(city_to_idx[dest])
            values_out.append(val)
            labels_out.append(f"${val:.2f}")
            colors_out.append(link_color)

    return sources_out, targets_out, values_out, labels_out, colors_out


# =====================================================================
# 6. Dash App
# =====================================================================
from main_page import app  # share the single server instance
server = app.server

layout = html.Div([

    html.H2(
        "✈️  NEURAL FLIGHT TRACKER — ROUTE PRICE SANKEY",
        style={
            "textAlign": "center",
            "color": NEON_CYAN,
            "textShadow": f"0 0 12px {NEON_CYAN}",
            "letterSpacing": "3px",
            "margin": "0 0 16px 0",
            "fontSize": "20px"
        }
    ),

    # ── Filter bar ────────────────────────────────────────────────────
    html.Div([

        # Back button — paste as first child of the layout Div
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


        # Source filter
        html.Div([
            html.Label("ORIGIN", style=LABEL_STYLE),
            dcc.Dropdown(
                id="filter-source",
                options=(
                        [{"label": "All Origins", "value": "ALL"}] +
                        [{"label": c, "value": c} for c in sources_cities]
                ),
                value="ALL",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "160px"}
            )
        ], style=FILTER_CELL),

        # Destination filter
        html.Div([
            html.Label("DESTINATION", style=LABEL_STYLE),
            dcc.Dropdown(
                id="filter-dest",
                options=(
                        [{"label": "All Destinations", "value": "ALL"}] +
                        [{"label": c, "value": c} for c in targets_cities]
                ),
                value="ALL",
                clearable=False,
                style={**DROPDOWN_STYLE, "width": "180px"}
            )
        ], style=FILTER_CELL),

        # Divider
        html.Span(style={
            "display": "inline-block", "width": "1px", "height": "44px",
            "backgroundColor": NEON_BLUE, "verticalAlign": "middle",
            "opacity": "0.4", "marginRight": "20px"
        }),

        # Stat method toggle
        html.Div([
            html.Label("PRICE STATISTIC", style=LABEL_STYLE),
            dcc.RadioItems(
                id="filter-stat",
                options=[
                    {"label": "  Mean",   "value": "mean"},
                    {"label": "  Median", "value": "median"}
                ],
                value="mean",
                labelStyle={
                    "display": "inline-block",
                    "color": TEXT_MUTED,
                    "marginRight": "16px",
                    "fontSize": "13px"
                }
            )
        ], style=FILTER_CELL),

    ], style={
        "backgroundColor": PANEL_BG,
        "padding": "12px 20px",
        "borderRadius": "12px",
        "marginBottom": "16px",
        "boxShadow": f"0 0 16px {NEON_BLUE}50",
        "display": "flex",
        "alignItems": "center",
        "flexWrap": "wrap"
    }),

    # ── Stats summary row ─────────────────────────────────────────────
    html.Div(id="stats-bar", style={
        "backgroundColor": PANEL_BG,
        "padding": "10px 20px",
        "borderRadius": "10px",
        "marginBottom": "14px",
        "fontSize": "12px",
        "color": TEXT_MUTED,
        "boxShadow": f"0 0 10px {NEON_BLUE}30",
        "overflowX": "auto",
        "whiteSpace": "nowrap"
    }),

    # ── Sankey chart ──────────────────────────────────────────────────
    html.Div([
        dcc.Graph(
            id="sankey-chart",
            style={"height": "72vh", "width": "100%"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={
        "borderRadius": "15px",
        "overflow": "hidden",
        "boxShadow": f"0 0 20px {NEON_CYAN}40"
    })

], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "22px 26px",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "boxSizing": "border-box"
})

# =====================================================================
# 7. Callbacks
# =====================================================================
@app.callback(
    Output("sankey-chart", "figure"),
    Output("stats-bar",    "children"),
    Input("filter-source", "value"),
    Input("filter-dest",   "value"),
    Input("filter-stat",   "value")
)
def update_sankey(selected_source, selected_dest, stat_method):

    # Resolve which sources/destinations are active
    active_sources = sources_cities if selected_source == "ALL" else [selected_source]
    active_targets = targets_cities if selected_dest   == "ALL" else [selected_dest]

    # Pick the right price table and link colour
    if stat_method == "mean":
        price_tbl  = mean_table
        link_color = LINK_COLOR_MEAN
        stat_label = "MEAN"
        stat_color = NEON_CYAN
    else:
        price_tbl  = median_table
        link_color = LINK_COLOR_MEDIAN
        stat_label = "MEDIAN"
        stat_color = NEON_PINK

    # When a single destination is selected we zero-out all other dest columns
    # so only the chosen route appears in the diagram
    if selected_dest != "ALL":
        filtered_table = []
        for j, dest in enumerate(targets_cities):
            row = []
            for i, src in enumerate(sources_cities):
                if dest == selected_dest:
                    row.append(price_tbl[j][i])
                else:
                    row.append(0.0)
            filtered_table.append(row)
    else:
        filtered_table = price_tbl

    src_list, tgt_list, val_list, lbl_list, col_list = build_links(
        active_sources, filtered_table, link_color
    )

    if not val_list:
        # Nothing to show
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=PANEL_BG,
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_MUTED),
            title=dict(text="NO DATA FOR SELECTED FILTERS",
                       font=dict(color=NEON_PINK))
        )
        return fig, "No data available for the selected combination."

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20,
            thickness=22,
            line=dict(color="#0b0c10", width=1),
            label=nodes,
            color=node_colors,
            hovertemplate="<b>%{label}</b><extra></extra>"
        ),
        link=dict(
            source=src_list,
            target=tgt_list,
            value=val_list,
            label=lbl_list,
            color=col_list,
            hovertemplate=(
                "<b>%{source.label} → %{target.label}</b><br>"
                f"{stat_label} price: $%{{value:.2f}}<br>"
                "<extra></extra>"
            )
        )
    ))

    # Build title
    src_part  = selected_source if selected_source != "ALL" else "All Origins"
    dest_part = selected_dest   if selected_dest   != "ALL" else "All Destinations"
    title_txt = (
        f"ROUTE PRICE SANKEY  |  {src_part} → {dest_part}  "
        f"|  <span style='color:{stat_color}'>{stat_label}</span>"
    )

    fig.update_layout(
        title=dict(text=title_txt, font=dict(color=NEON_CYAN, size=14)),
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI", size=13),
        margin=dict(l=30, r=30, t=55, b=30),
        height=None   # let the container control height
    )

    # ── Stats summary bar content ──────────────────────────────────────
    stats_items = []
    for src in active_sources:
        for dest in active_targets:
            m  = route_mean.get((src, dest), np.nan)
            md = route_median.get((src, dest), np.nan)
            n  = route_counts.get((src, dest), 0)
            if np.isnan(m):
                continue
            diff      = m - md
            diff_sign = "+" if diff >= 0 else "-"
            highlight = stat_color if stat_method == "mean" else TEXT_MUTED
            h_med     = stat_color if stat_method == "median" else TEXT_MUTED

            stats_items.append(
                html.Span([
                    html.Span(f"{src}→{dest}",
                              style={"color": NEON_CYAN, "fontWeight": "bold",
                                     "marginRight": "6px"}),
                    html.Span(f"mean ${m:.2f}",
                              style={"color": highlight, "marginRight": "4px"}),
                    html.Span(f"median ${md:.2f}",
                              style={"color": h_med, "marginRight": "4px"}),
                    html.Span(f"Δ {diff_sign}${abs(diff):.2f}",
                              style={"color": NEON_YELLOW, "marginRight": "4px"}),
                    html.Span(f"n={n}",
                              style={"color": "#555", "marginRight": "24px"}),
                ])
            )

    stats_content = stats_items if stats_items else "No statistics available."
    return fig, stats_content


# =====================================================================
# 8. Run
# =====================================================================
# Remove or comment out:
if __name__ == '__main__':
    app.run(debug=True)