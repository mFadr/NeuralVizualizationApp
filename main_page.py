import os
import uuid
import pandas as pd
import numpy as np
from dash import html, dcc, Input, Output, State, callback_context
from flask import request
from app_instance import app, server
from config import DATASET_PATHS

# === NOVÉ === Import sledovacího modulu
from analytics import init_db, log_visit, get_stats, PATH_LABELS

# Inicializace databáze při startu
init_db()

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

# === Výpočet KPI === (beze změny)
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
        "canceled":      int(canceled_count) if total_records > 0 else 0,
    }

KPI = compute_kpis()


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


# === NOVÁ FUNKCE === Vytvoření tabulky s analytikami návštěvnosti
def make_analytics_panel():
    stats = get_stats()

    # Hlavička s celkovými ukazateli
    header_row = html.Div([
        html.Div([
            html.Div("TOTAL VISITS", style={
                "color": NEON_BLUE, "fontSize": "8px",
                "letterSpacing": "2px"
            }),
            html.Div(f"{stats['total']:,}", style={
                "color": NEON_CYAN, "fontSize": "18px",
                "fontWeight": "bold",
                "textShadow": f"0 0 6px {NEON_CYAN}"
            })
        ], style={"flex": "1", "textAlign": "center"}),

        html.Div([
            html.Div("LAST 24H", style={
                "color": NEON_BLUE, "fontSize": "8px",
                "letterSpacing": "2px"
            }),
            html.Div(f"{stats['last_24h']:,}", style={
                "color": "#39ff14", "fontSize": "18px",
                "fontWeight": "bold",
                "textShadow": "0 0 6px #39ff14"
            })
        ], style={"flex": "1", "textAlign": "center"}),

        html.Div([
            html.Div("UNIQUE / 7D", style={
                "color": NEON_BLUE, "fontSize": "8px",
                "letterSpacing": "2px"
            }),
            html.Div(f"{stats['unique_7d']:,}", style={
                "color": NEON_PINK, "fontSize": "18px",
                "fontWeight": "bold",
                "textShadow": f"0 0 6px {NEON_PINK}"
            })
        ], style={"flex": "1", "textAlign": "center"})
    ], style={
        "display": "flex", "gap": "12px",
        "marginBottom": "12px",
        "paddingBottom": "10px",
        "borderBottom": f"1px solid {NEON_BLUE}20",
        "paddingRight": "250px"  # ← Changed from 60px to ~250px (60 + 190)
    })

    # Tabulka popularity modulů
    if not stats["modules"]:
        module_rows = [html.Div("No traffic data yet", style={
            "color": TEXT_MUTED, "fontSize": "10px",
            "textAlign": "center", "padding": "8px"
        })]
    else:
        max_visits = max(m["visits"] for m in stats["modules"]) or 1
        module_rows = []
        for m in stats["modules"]:
            label    = PATH_LABELS.get(m["path"], m["path"])
            width_pc = (m["visits"] / max_visits) * 100
            module_rows.append(html.Div([
                html.Div([
                    html.Span(label, style={
                        "color": NEON_CYAN, "fontSize": "10px",
                        "fontFamily": "Courier New, monospace"
                    }),
                    html.Span(f"{m['visits']:,} hits", style={
                        "color": TEXT_MUTED, "fontSize": "10px",
                        "fontFamily": "Courier New, monospace",
                        "float": "right"
                    })
                ], style={"marginBottom": "3px"}),
                html.Div(style={
                    "width": f"{width_pc}%",
                    "height": "4px",
                    "backgroundColor": NEON_CYAN,
                    "boxShadow": f"0 0 4px {NEON_CYAN}",
                    "borderRadius": "2px"
                })
            ], style={"marginBottom": "6px"}))

    return html.Div([
        html.Div("◈  TRAFFIC ANALYTICS  //  MODULE POPULARITY", style={
            "color":         NEON_BLUE,
            "fontSize":      "9px",
            "letterSpacing": "3px",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "10px"
        }),
        html.Div([
            # Neviditelný spacer na levé straně
            html.Div(module_rows, style={
                "flex": "1"
            }),
            # Střed - header_row
            html.Div(header_row, style={
                "flex": "1",
                "display": "flex",
                "justifyContent": "center"
            }),
            # Neviditelný spacer na pravé straně
            html.Div(style={
                "flex": "1",
                "visibility": "hidden"
            })
        ], style={
            "display": "flex",
            "gap": "12px"
        })
    ], style={
        "padding":         "12px 16px",
        "backgroundColor": PANEL_BG,
        "borderRadius":    "10px",
        "border":          f"1px solid {NEON_PINK}30",
        "boxShadow":       f"0 0 12px {NEON_PINK}15",
        "marginBottom":    "28px"
    })


def make_footer():
    """Sestavení zápatí (footeru) hlavní stránky aplikace."""
    return html.Div([
        # Tenká červená dělící linka nad textem footeru
        html.Div(style={
            "height":          "2px",
            "width":           "100%",
            "background":      "linear-gradient(90deg, transparent 0%, #ff3366 20%, #ff007f 50%, #ff3366 80%, transparent 100%)",
            "boxShadow":       "0 0 10px #ff007f",
            "marginBottom":    "16px"
        }),

        # Hlavní řádek s textem footeru
        html.Div([
            html.Span("© 2026 ", style={"color": TEXT_MUTED}),
            html.Span("Flight Analytics Platform ", style={
                "color":      NEON_CYAN,
                "fontWeight": "bold",
                "textShadow": f"0 0 6px {NEON_CYAN}"
            }),
            html.Span("by ", style={"color": TEXT_MUTED}),
            html.Span("[Jméno autora] ", style={
                "color":      NEON_CYAN,
                "fontWeight": "bold"
            }),
            html.Span(" |  ", style={"color": NEON_BLUE}),
            html.Span("All Rights Reserved", style={"color": TEXT_MUTED}),
            html.Span("  |  ", style={"color": NEON_BLUE}),
            html.Span("Powered by ", style={"color": TEXT_MUTED}),
            html.A("Plotly Dash", href="https://plotly.com/dash/",
                   target="_blank",
                   style={
                       "color":          NEON_PINK,
                       "textDecoration": "none",
                       "fontWeight":     "bold",
                       "textShadow":     f"0 0 6px {NEON_PINK}"
                   }),
            html.Span(" & ", style={"color": TEXT_MUTED}),
            html.A("Pandas", href="https://pandas.pydata.org/",
                   target="_blank",
                   style={
                       "color":          NEON_PINK,
                       "textDecoration": "none",
                       "fontWeight":     "bold"
                   })
        ], style={
            "fontSize":      "11px",
            "letterSpacing": "1px",
            "fontFamily":    "Courier New, monospace",
            "textAlign":     "center",
            "marginBottom":  "10px"
        }),

        # Druhý řádek s informací o akademickém kontextu práce
        html.Div([
            html.Span("Bakalářská práce  //  ", style={"color": NEON_BLUE}),
            html.Span("Analýza a vizualizace vývoje cen letenek na vybraných trasách leteckých společností",
                      style={"color": TEXT_MUTED, "fontStyle": "italic"})
        ], style={
            "fontSize":      "10px",
            "letterSpacing": "1px",
            "fontFamily":    "Courier New, monospace",
            "textAlign":     "center",
            "marginBottom":  "8px"
        }),

        # Třetí řádek s informačním upozorněním
        html.Div([
            html.Span("Data sesbírána v lednu 2026  //  Vizualizace slouží výhradně k akademickým a vzdělávacím účelům",
                      style={"color": TEXT_MUTED, "opacity": "0.7"})
        ], style={
            "fontSize":      "9px",
            "letterSpacing": "1px",
            "fontFamily":    "Courier New, monospace",
            "textAlign":     "center",
            "marginBottom":  "8px"
        }),

        # Čtvrtý řádek s odkazem na repozitář
        html.Div([
            html.A("GitHub repozitář",
                   href="https://github.com/[uživatelské-jméno]/[název-repozitáře]",
                   target="_blank",
                   style={
                       "color":          NEON_BLUE,
                       "textDecoration": "none",
                       "fontSize":       "9px",
                       "letterSpacing":  "2px"
                   })
        ], style={
            "textAlign":  "center",
            "fontFamily": "Courier New, monospace"
        })

    ], style={
        "width":         "100%",
        "padding":       "24px 20px 18px 20px",
        "marginTop":     "60px",
        "borderTop":     "1px solid #1f2833",
        "backgroundColor": "#08090d",
        "boxSizing":     "border-box"
    })


def build_main_layout():
    """Sestavení hlavního layoutu, aby se analytiky obnovovaly při každé návštěvě."""
    return html.Div([
        html.Div([
            html.H1("✈  FLIGHT ANALYTICS PLATFORM", style={
                "color":        NEON_CYAN,
                "textShadow":   f"0 0 20px {NEON_CYAN}",
                "letterSpacing":"5px",
                "fontSize":     "22px",
                "fontFamily":   "Courier New, monospace",
                "margin":       "0 0 150px 0",
                "width":        "100%",
                "textAlign":    "center"
            }),
            html.Div("CENTRAL OPERATIONS  //  SELECT MODULE", style={
                "color":         NEON_BLUE,
                "fontSize":      "10px",
                "letterSpacing": "4px",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "28px"
            }),

            # Hlavní flex layout s levým panelem analytiky a pravým obsahem s KPI
            html.Div([
                # Levý panel - Analytics panel jako vertikální banner
                html.Div([
                    make_analytics_panel(),
                ], style={
                    "width":       "20%",
                    "marginRight": "24px"
                }),

                # Pravý panel - Obsah a karty modulů
                html.Div([
                    # KPI karty - horizontální orientace
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
                        "display":        "flex",
                        "flexWrap":       "wrap",
                        "gap":            "12px",
                        "marginBottom":   "20px"
                    }),

                    # Stávající stavová lišta
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
                        "marginBottom": "20px",
                        "padding":      "12px 16px",
                        "backgroundColor": PANEL_BG,
                        "borderRadius": "10px",
                        "border":       f"1px solid {NEON_BLUE}20",
                        "boxShadow":    f"0 0 12px {NEON_BLUE}20"
                    }),


                    # Karty modulů - 3+3 layout
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
                            "gridTemplateColumns": "1fr 1fr 1fr",
                            "gap":                 "20px",
                            "width":               "100%"
                        }
                    )
                ], style={
                    "flex": "1"
                })
            ], style={
                "display":   "flex",
                "gap":       "20px",
                "width":     "100%"
            })

        ], style={
            "textAlign": "center",
            "maxWidth":  "960px",
            "margin":    "0 auto",
            "width":     "100%"
        }),

        # Footer připojený pod hlavní obsah
        make_footer()

    ], style={
        "backgroundColor": BG_COLOR,
        "minHeight":       "100vh",
        "display":         "flex",
        "flexDirection":   "column",
        "alignItems":      "center",
        "justifyContent":  "flex-start",
        "padding":         "32px 24px 0 24px",
        "fontFamily":      "Courier New, monospace"
    })


# === Hlavní layout === se skrytým úložištěm pro session_id
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="local"),
    html.Div(id="page-content")
])


# === ROUTING + SLEDOVÁNÍ ===
@app.callback(
    Output("page-content", "children"),
    Output("session-store", "data"),
    Input("url", "pathname"),
    State("session-store", "data")
)
def route(pathname, session_data):
    # Zajištění session_id (přiřazeno klientovi navždy v lokálním úložišti)
    if not session_data or "sid" not in session_data:
        session_data = {"sid": str(uuid.uuid4())}
    sid = session_data["sid"]

    # Získání user agenta z požadavku Flask
    user_agent = None
    try:
        user_agent = request.headers.get("User-Agent", "")[:200]
    except RuntimeError:
        # Mimo kontext požadavku
        pass

    # Záznam návštěvy
    log_visit(pathname or "/", session_id=sid, user_agent=user_agent)

    # Vrácení obsahu stránky
    if pathname == "/offers":
        import vizualizationFlightOffers
        return vizualizationFlightOffers.layout, session_data

    if pathname == "/january":
        import vizualizationJanuary
        return vizualizationJanuary.layout, session_data

    if pathname == "/emission":
        import vizualizationEmision
        return vizualizationEmision.layout, session_data

    if pathname == "/sankey":
        import vizualizationSankey
        return vizualizationSankey.layout, session_data

    if pathname == "/gini":
        import vizualizationGini
        return vizualizationGini.layout, session_data

    if pathname == "/info":
        import vizualizationManual
        return vizualizationManual.layout, session_data

    return build_main_layout(), session_data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
