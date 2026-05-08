import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# =====================================================================
# 1. Konfigurace
# =====================================================================

from config import DATASET_PATHS

sources_cities = ["PRG", "WAW", "BER", "VIE", "BUD"]
targets_cities = ["FCO", "BCN", "LON", "AMS"]

# =====================================================================
# 2. Cyberpunk téma
# =====================================================================
BG_COLOR    = "#0b0c10"
PANEL_BG    = "#1f2833"
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_YELLOW = "#f5c518"
TEXT_MUTED  = "#c5c6c7"

# Barvy uzlů: zdroje = tyrkysová paleta, cíle = růžová paleta
SOURCE_COLORS = ["#66fcf1", "#45a29e", "#00b4d8", "#0077b6", "#023e8a"]
TARGET_COLORS = ["#ff007f", "#c9184a", "#ff4d6d", "#ff758f"]

# Barvy spojení podle statistické metody (poloprůhledné)
LINK_COLOR_MEAN   = "rgba(102,252,241,0.25)"   # tyrkysový odstín
LINK_COLOR_MEDIAN = "rgba(255,0,127,0.25)"      # růžový odstín

DROPDOWN_STYLE = {"color": "black"}
LABEL_STYLE = {
    "color": NEON_BLUE, "fontSize": "10px",
    "letterSpacing": "1px", "marginBottom": "4px", "display": "block"
}
FILTER_CELL = {"display": "inline-block", "verticalAlign": "top", "marginRight": "20px"}

# Styl pro vícenásobné zaškrtávací pole filtrů (sloupec)
CHECKLIST_STYLE = {
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "4px"
}
CHECKLIST_LABEL_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "color": TEXT_MUTED,
    "fontSize": "12px",
    "marginRight": "0px",
    "padding": "2px 6px",
    "borderRadius": "4px"
}
CHECKLIST_INPUT_STYLE = {"marginRight": "6px", "accentColor": NEON_CYAN}

# =====================================================================
# 3. Načtení a výpočet statistik jednotlivých tras z reálných CSV souborů
# =====================================================================
def load_form_csv(path):
    """Load a _form.csv and return cleaned DataFrame."""
    df = pd.read_csv(path, sep=r"[\t;,]", engine="python")
    df.columns = df.columns.str.strip().str.lower()

    # Normalizace názvu sloupce destination
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

    # Sjednocený sloupec stavu letu (flown / flight canceled / ...).
    # Pokud sloupec ve zdroji chybí, předpokládá se, že všechny záznamy byly odlétnuty.
    if "flown_status" in df.columns:
        df["_status_col"] = df["flown_status"].astype(str).str.lower().str.strip()
    else:
        df["_status_col"] = "flown"
    return df


def compute_route_stats(dataset_paths, sources, targets):
    """
    For every (origin, destination) pair compute mean and median
    from the real scraped price records, in two parallel modes:

      * "all"   → all rows (including flight canceled)
      * "flown" → only rows with flown_status == "flown"

    Returns a dict keyed by mode, each containing three dicts
    keyed by (origin, destination):
        route_mean[mode]   → float
        route_median[mode] → float
        route_counts[mode] → int
    """
    modes = ("all", "flown")
    route_mean   = {m: {} for m in modes}
    route_median = {m: {} for m in modes}
    route_counts = {m: {} for m in modes}

    for origin, path in dataset_paths.items():
        if origin not in sources:
            continue
        try:
            df_full = load_form_csv(path)
        except Exception as e:
            print(f"✗ Could not load {origin} from {path}: {e}")
            # Vyplní NaN pro oba režimy, aby se diagram i tak vykreslil
            for m in modes:
                for dest in targets:
                    route_mean[m][(origin, dest)]   = np.nan
                    route_median[m][(origin, dest)] = np.nan
                    route_counts[m][(origin, dest)] = 0
            continue

        # Připraví dvě verze datového rámce: vše a pouze odlétnuté lety
        df_by_mode = {
            "all":   df_full,
            "flown": df_full[df_full["_status_col"] == "flown"]
            if "_status_col" in df_full.columns else df_full
        }

        for m, df in df_by_mode.items():
            for dest in targets:
                prices = df.loc[df["destination"] == dest, "price"].dropna()
                n = len(prices)
                route_counts[m][(origin, dest)] = n
                if n > 0:
                    route_mean[m][(origin, dest)]   = float(prices.mean())
                    route_median[m][(origin, dest)] = float(prices.median())
                else:
                    route_mean[m][(origin, dest)]   = np.nan
                    route_median[m][(origin, dest)] = np.nan
                if m == "all":
                    print(
                        f"  {origin}→{dest}: n_all={n:>5}  "
                        f"mean=${route_mean[m][(origin,dest)]:.2f}  "
                        f"median=${route_median[m][(origin,dest)]:.2f}"
                        if n > 0 else
                        f"  {origin}→{dest}: NO DATA"
                    )

    return route_mean, route_median, route_counts


print("Počítám statistiky tras z reálných dat (režimy: vše, uskutečněné)...")
route_mean, route_median, route_counts = compute_route_stats(
    DATASET_PATHS, sources_cities, targets_cities
)
print("Hotovo.\n")

# =====================================================================
# 4. Sestavení cenových tabulek z vypočtených statistik
#    Rozložení: price_table[dest_idx][src_idx]  (stejné jako původně)
# =====================================================================
def build_price_table(stat_dict, sources, targets):
    """Convert route stat dict → 2-D list [dest][source]."""
    table = []
    for dest in targets:
        row = []
        for src in sources:
            val = stat_dict.get((src, dest), np.nan)
            row.append(val if not np.isnan(val) else 0.0)  # 0 = neviditelné spojení
        table.append(row)
    return table


mean_table = {
    m: build_price_table(route_mean[m],   sources_cities, targets_cities)
    for m in ("all", "flown")
}
median_table = {
    m: build_price_table(route_median[m], sources_cities, targets_cities)
    for m in ("all", "flown")
}

# =====================================================================
# 5. Sestavení spojení Sankey grafu
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
# 6. Dash aplikace
# =====================================================================
from app_instance import app # sdílí jedinou instanci serveru
server = app.server

layout = html.Div([

    html.Div([
        html.H2(
            "✈️  Neural flight tracker — Sankey diagram cen tras",
            style={
                "textAlign": "center",
                "color": NEON_CYAN,
                "textShadow": f"0 0 12px {NEON_CYAN}",
                "letterSpacing": "3px",
                "margin": "0 0 16px 0",
                "fontSize": "20px",
                "display": "inline-block",
                "width": "calc(100% - 100px)"
            }
        ),
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
    ], style={"position": "relative", "marginBottom": "16px"}),

    # ── Sankey graf ───────────────────────────────────────────────────
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
    }),

    # ── Lišta filtrů ───────────────────────────────────────────────────
    html.Div([

        # Vícenásobné zaškrtávací pole pro výchozí letiště a destinace
        # uspořádaná do dvou sloupců vedle sebe
        html.Div([
            # Sloupec 1: Výchozí letiště
            html.Div([
                html.Label("Výchozí letiště", style=LABEL_STYLE),
                dcc.Checklist(
                    id="filter-source",
                    options=[{"label": c, "value": c} for c in sources_cities],
                    value=list(sources_cities),
                    labelStyle=CHECKLIST_LABEL_STYLE,
                    inputStyle=CHECKLIST_INPUT_STYLE,
                    style=CHECKLIST_STYLE
                )
            ], style={**FILTER_CELL, "minWidth": "150px"}),

            # Sloupec 2: Destinace
            html.Div([
                html.Label("Destinace", style=LABEL_STYLE),
                dcc.Checklist(
                    id="filter-dest",
                    options=[{"label": c, "value": c} for c in targets_cities],
                    value=list(targets_cities),
                    labelStyle=CHECKLIST_LABEL_STYLE,
                    inputStyle=CHECKLIST_INPUT_STYLE,
                    style=CHECKLIST_STYLE
                )
            ], style={**FILTER_CELL, "minWidth": "150px"}),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "gap": "20px",
            "marginRight": "20px",
            "verticalAlign": "top"
        }),

        # Oddělovač
        html.Span(style={
            "display": "inline-block", "width": "1px", "height": "44px",
            "backgroundColor": NEON_BLUE, "verticalAlign": "middle",
            "opacity": "0.4", "marginRight": "20px"
        }),


        # Přepínač datového rozsahu (zrušené lety ANO/NE)
        html.Div([
            html.Label("Rozsah dat", style=LABEL_STYLE),
            dcc.RadioItems(
                id="filter-status",
                options=[
                    {"label": "  Se zrušenými lety",    "value": "all"},
                    {"label": "  Bez zrušených letů", "value": "flown"}
                ],
                value="all",
                labelStyle={
                    "display": "inline-block",
                    "color": TEXT_MUTED,
                    "marginRight": "16px",
                    "fontSize": "13px"
                },
                inputStyle={"marginRight": "6px", "accentColor": NEON_CYAN}
            )
        ], style=FILTER_CELL),


        # Přepínač statistické metody
        html.Div([
            html.Label("Cenová statistika", style=LABEL_STYLE),
            dcc.RadioItems(
                id="filter-stat",
                options=[
                    {"label": "  Průměr",   "value": "mean"},
                    {"label": "  Medián", "value": "median"}
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

    # ── Řádek souhrnných statistik ─────────────────────────────────────
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
# 7. Callbacky
# =====================================================================
@app.callback(
    Output("sankey-chart", "figure"),
    Output("stats-bar",    "children"),
    Input("filter-source", "value"),
    Input("filter-dest",   "value"),
    Input("filter-stat",   "value"),
    Input("filter-status", "value")
)
def update_sankey(selected_source, selected_dest, stat_method, status):

    # dcc.Checklist vrací seznam vybraných hodnot (může být i prázdný nebo None)
    selected_source = selected_source or []
    selected_dest   = selected_dest   or []

    # Určí, které zdroje/destinace jsou aktivní (zachová pořadí podle původních seznamů)
    active_sources = [s for s in sources_cities if s in selected_source]
    active_targets = [t for t in targets_cities if t in selected_dest]

    # Datový režim: "all" (vše) nebo "flown" (pouze odlétnuté lety)
    mode = status if status in ("all", "flown") else "all"

    # Vybere správnou cenovou tabulku a barvu spojení
    if stat_method == "mean":
        price_tbl  = mean_table[mode]
        link_color = LINK_COLOR_MEAN
        stat_label = "Aritmetický průměr"
        stat_color = NEON_CYAN
    else:
        price_tbl  = median_table[mode]
        link_color = LINK_COLOR_MEDIAN
        stat_label = "Medián"
        stat_color = NEON_PINK

    # Filtrace cenové tabulky: vynuluje sloupce destinací, které nejsou aktivní,
    # aby se v diagramu zobrazily pouze zvolené trasy
    filtered_table = []
    for j, dest in enumerate(targets_cities):
        row = []
        for i, src in enumerate(sources_cities):
            if dest in active_targets:
                row.append(price_tbl[j][i])
            else:
                row.append(0.0)
        filtered_table.append(row)

    src_list, tgt_list, val_list, lbl_list, col_list = build_links(
        active_sources, filtered_table, link_color
    )

    if not val_list:
        # Nic k zobrazení
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=PANEL_BG,
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_MUTED),
            title=dict(text="Žádná data pro vybrané filtry",
                       font=dict(color=NEON_PINK))
        )
        return fig, "Pro vybranou kombinaci nejsou k dispozici žádná data."

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
                f"{stat_label} - cena: $%{{value:.2f}}<br>"
                "<extra></extra>"
            )
        )
    ))

    # Sestaví titulek
    if not active_sources:
        src_part = "Žádné výchozí letiště"
    elif len(active_sources) == len(sources_cities):
        src_part = "Všechna výchozí letiště"
    else:
        src_part = ", ".join(active_sources)

    if not active_targets:
        dest_part = "Žádná destinace"
    elif len(active_targets) == len(targets_cities):
        dest_part = "Všechny destinace"
    else:
        dest_part = ", ".join(active_targets)

    title_txt = (
        f"Sankey diagram cen tras  |  {src_part} → {dest_part}  "
        f"|  <span style='color:{stat_color}'>{stat_label}</span>"
    )

    fig.update_layout(
        title=dict(text=title_txt, font=dict(color=NEON_CYAN, size=14)),
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI", size=13),
        margin=dict(l=30, r=30, t=55, b=30),
        height=None   # výšku nechá řídit kontejner
    )

    # ── Obsah lišty souhrnných statistik ───────────────────────────────
    stats_items = []
    for src in active_sources:
        for dest in active_targets:
            m  = route_mean[mode].get((src, dest), np.nan)
            md = route_median[mode].get((src, dest), np.nan)
            n  = route_counts[mode].get((src, dest), 0)
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
                    html.Span(f"průměr ${m:.2f}",
                              style={"color": highlight, "marginRight": "4px"}),
                    html.Span(f"medián ${md:.2f}",
                              style={"color": h_med, "marginRight": "4px"}),
                    html.Span(f"Δ {diff_sign}${abs(diff):.2f}",
                              style={"color": NEON_YELLOW, "marginRight": "4px"}),
                    html.Span(f"n={n}",
                              style={"color": "#555", "marginRight": "24px"}),
                ])
            )

    stats_content = stats_items if stats_items else "Žádné statistiky nejsou k dispozici."
    return fig, stats_content


# =====================================================================
# 8. Spuštění
# =====================================================================
# Odstraňte nebo zakomentujte:
if __name__ == '__main__':
    app.run(debug=True)
