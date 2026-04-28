import os
import pandas as pd
import numpy as np
from dash import html, dcc, Input, Output
from app_instance import app, server   
from config import DATASET_PATHS



BG_COLOR    = "#0b0c10"
PANEL_BG    = "#1f2833"
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_PURPLE = "#9d4edd"
TEXT_MUTED  = "#c5c6c7"

PAGES = [
    {
        "title":    "BOOKING CURVE ANALYZER",
        "subtitle": "Price trends over the scraping period",
        "href":     "/offers",
        "accent":   NEON_CYAN,
        "icon":     "📈"
    },
    {
        "title":    "JANUARY FLIGHT TRACKER",
        "subtitle": "Multi-origin price comparison — Jan 2026",
        "href":     "/january",
        "accent":   NEON_PINK,
        "icon":     "✈️"
    },
    {
        "title":    "EMISSION INTELLIGENCE",
        "subtitle": "CO₂ and per-seat emission analysis",
        "href":     "/emission",
        "accent":   "#39ff14",
        "icon":     "🌍"
    },
    {
        "title":    "ROUTE SANKEY",
        "subtitle": "Flow diagram of prices between cities",
        "href":     "/sankey",
        "accent":   "#f5c518",
        "icon":     "🗺️"
    },
    {
        "title":    "GINI ANALYZER",
        "subtitle": "Inequality analysis of price distributions",
        "href":     "/gini",
        "accent":   NEON_PURPLE,
        "icon":     "📊"
    },
    {
        "title":    "Manual",
        "subtitle": "How to use the platform and interpret the data",
        "href":     "/info",
        "accent":   NEON_PURPLE,
        "icon":     "📊"
    },
]

# Výpočet KPI — spouští se jednou při spuštění

def compute_kpis():
    total_records  = 0
    total_routes   = set()
    all_prices     = []
    canceled_count = 0
    origins_loaded = 0

    for origin, path in DATASET_PATHS.items():
        try:
            df = pd.read_csv(path, sep=r"[\t;,]", engine="python")
            df.columns = df.columns.str.strip().str.lower()
            total_records  += len(df)
            origins_loaded += 1

            dest_col = next((c for c in df.columns
                             if c in ("destination", "dest")), None)
            if dest_col:
                for d in df[dest_col].dropna().unique():
                    total_routes.add(f"{origin}-{str(d).upper()}")

            price_col = next((c for c in df.columns if "price" in c), None)
            if price_col:
                prices = pd.to_numeric(
                    df[price_col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                    errors="coerce"
                ).dropna()
                all_prices.extend(prices.tolist())

            for col in df.columns:
                if any(k in col for k in ("status", "canceled", "cancelled")):
                    canceled_count += df[col].astype(str).str.contains(
                        "CANCEL", case=False, na=False
                    ).sum()
                    break

        except Exception:
            pass

    return {
        "origins":       origins_loaded,
        "total_records": total_records,
        "total_routes":  len(total_routes),
        "avg_price":     round(float(np.mean(all_prices)), 2) if all_prices else 0,
        "min_price":     round(float(np.min(all_prices)),  2) if all_prices else 0,
        "max_price":     round(float(np.max(all_prices)),  2) if all_prices else 0,
        "canceled":      int(canceled_count)
        if total_records > 0 else 0,
    }

KPI = compute_kpis()

# Rozložení hlavní stránky
def make_kpi_card(label, value, unit="", accent=NEON_CYAN):
    return html.Div([
        html.Div(label, style={
            "color":         NEON_BLUE,
            "fontSize":      "9px",
            "letterSpacing": "2px",
            "marginBottom":  "6px",
            "fontFamily":    "Courier New, monospace"
        }),
        html.Div([
            html.Span(str(value), style={
                "color":      accent,
                "fontSize":   "22px",
                "fontWeight": "bold",
                "fontFamily": "Courier New, monospace",
                "textShadow": f"0 0 8px {accent}"
            }),
            html.Span(f" {unit}", style={
                "color":    TEXT_MUTED,
                "fontSize": "10px",
                "fontFamily": "Courier New, monospace"
            })
        ])
    ], style={
        "backgroundColor": PANEL_BG,
        "border":          f"1px solid {accent}30",
        "borderRadius":    "10px",
        "padding":         "14px 18px",
        "flex":            "1",
        "minWidth":        "120px",
        "boxShadow":       f"0 0 10px {accent}15"
    })


def make_card(page):
    return html.A(
        href=page["href"],
        style={"textDecoration": "none", "display": "block", "height": "100%"},
        children=html.Div([
            html.Div(page["icon"], style={
                "fontSize": "30px", "marginBottom": "10px"
            }),
            html.Div(page["title"], style={
                "color":        page["accent"],
                "fontSize":     "12px",
                "letterSpacing":"2px",
                "fontWeight":   "bold",
                "marginBottom": "6px",
                "fontFamily":   "Courier New, monospace",
                "textShadow":   f"0 0 8px {page['accent']}"
            }),
            html.Div(page["subtitle"], style={
                "color":      TEXT_MUTED,
                "fontSize":   "10px",
                "fontFamily": "Courier New, monospace"
            })
        ], style={
            "backgroundColor": PANEL_BG,
            "border":          f"1px solid {page['accent']}40",
            "borderRadius":    "12px",
            "padding":         "28px 20px",
            "textAlign":       "center",
            "boxShadow":       f"0 0 18px {page['accent']}20",
            "cursor":          "pointer",
            "height":          "100%",
            "boxSizing":       "border-box"
        })
    )


main_layout = html.Div([
    html.Div([

        # Nadpis
        html.H1("✈  FLIGHT ANALYTICS PLATFORM", style={
            "color":        NEON_CYAN,
            "textShadow":   f"0 0 20px {NEON_CYAN}",
            "letterSpacing":"5px",
            "fontSize":     "22px",
            "fontFamily":   "Courier New, monospace",
            "margin":       "0 0 4px 0"
        }),
        html.Div("CENTRAL OPERATIONS  //  SELECT MODULE", style={
            "color":         NEON_BLUE,
            "fontSize":      "10px",
            "letterSpacing": "4px",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "28px"
        }),

        # KPI tabulky
        html.Div([
            make_kpi_card("ORIGIN AIRPORTS",   KPI["origins"],
                          "origins",  NEON_CYAN),
            make_kpi_card("TOTAL RECORDS",     f"{KPI['total_records']:,}",
                          "rows",     NEON_BLUE),
            make_kpi_card("ROUTES TRACKED",    KPI["total_routes"],
                          "routes",   NEON_PURPLE),
            make_kpi_card("AVG TICKET PRICE",  f"${KPI['avg_price']}",
                          "USD",      "#f5c518"),
            make_kpi_card("PRICE RANGE",
                          f"${KPI['min_price']}–${KPI['max_price']}",
                          "USD",      "#39ff14"),
        ], style={
            "display":         "flex",
            "gap":             "12px",
            "flexWrap":        "wrap",
            "justifyContent":  "center",
            "marginBottom":    "28px"
        }),

        # Živé sledování dat
        html.Div([
            html.Div("◈  SYSTEM STATUS  //  DATA TRACKING", style={
                "color":         NEON_BLUE,
                "fontSize":      "9px",
                "letterSpacing": "3px",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "8px"
            }),
            html.Div([
                html.Span("▶  DATASETS LOADED  ", style={"color": NEON_CYAN}),
                html.Span(f"{KPI['origins']}/5 origins  ·  ",
                          style={"color": "#39ff14"}),
                html.Span(f"{KPI['total_records']:,} total records  ·  ",
                          style={"color": TEXT_MUTED}),
                html.Span(f"{KPI['total_routes']} routes tracked  ·  ",
                          style={"color": TEXT_MUTED}),
                html.Span(f"avg price ${KPI['avg_price']}  ·  ",
                          style={"color": "#f5c518"}),

            ], style={
                "fontSize":   "11px",
                "fontFamily": "Courier New, monospace",
                "padding":    "8px 12px",
                "backgroundColor": "#0d1117",
                "borderRadius":    "6px",
                "border":          f"1px solid {NEON_BLUE}30",
                "overflowX":  "auto",
                "whiteSpace": "nowrap"
            })
        ], style={
            "marginBottom": "28px",
            "padding":      "12px 16px",
            "backgroundColor": PANEL_BG,
            "borderRadius": "10px",
            "border":       f"1px solid {NEON_BLUE}20",
            "boxShadow":    f"0 0 12px {NEON_BLUE}20"
        }),

        # Karty modulů — 3 nahoře + 2 dole vycentrované
        html.Div(
            [make_card(p) for p in PAGES[:3]],
            style={
                "display":             "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap":                 "20px",
                "marginBottom":        "20px",
                "width":               "100%"
            }
        ),
        html.Div(
            [make_card(p) for p in PAGES[3:]],
            style={
                "display":             "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap":                 "20px",
                "width":               "60%",
                "margin":              "0 auto"
            }
        )

    ], style={
        "textAlign": "center",
        "maxWidth":  "960px",
        "margin":    "0 auto",
        "width":     "100%"
    })
], style={
    "backgroundColor": BG_COLOR,
    "minHeight":       "100vh",
    "display":         "flex",
    "alignItems":      "center",
    "justifyContent":  "center",
    "padding":         "32px 24px",
    "fontFamily":      "Courier New, monospace"
})

# Hlavní layout — směrovač URL
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Routing callback — načítá obsah podle URL
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def route(pathname):
    if pathname == "/offers":
        import vizualizationFlightOffers
        return vizualizationFlightOffers.layout

    if pathname == "/january":
        import vizualizationJanuary
        return vizualizationJanuary.layout

    if pathname == "/emission":
        import vizualizationEmision
        return vizualizationEmision.layout

    if pathname == "/sankey":
        import vizualizationSankey
        return vizualizationSankey.layout

    if pathname == "/gini":
        import vizualizationGini
        return vizualizationGini.layout

    if pathname == "/info":
        import vizualizationManual
        return vizualizationManual.layout

    return main_layout


# Spuštění serveru
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
