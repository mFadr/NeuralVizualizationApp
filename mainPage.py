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
KPI_BG      = "#0d1117"        # Tmavší pozadí pro neinteraktivní KPI dlaždice
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_PURPLE = "#9d4edd"
NEON_YELLOW = "#f5c518"
NEON_GREEN  = "#39ff14"
TEXT_MUTED  = "#c5c6c7"

PAGES = [
    {
        "title":    "Historie vývoje cen letenek",
        "subtitle": "Křivka vývoje cen letenek 09/2025–01/2026",
        "href":     "/offers",
        "accent":   NEON_CYAN,
        "icon":     "📈"
    },
    {
        "title":    "Porovnání cen letů z ledna 2026",
        "subtitle": "Srovnání cen napříč výchozími letišti",
        "href":     "/january",
        "accent":   NEON_PINK,
        "icon":     "✈️"
    },
    {
        "title":    "Analýza emisí jednotlivých letů",
        "subtitle": "Analýza emisí CO₂ pro jednotlivé typy letadel",
        "href":     "/emission",
        "accent":   NEON_GREEN,
        "icon":     "🌍"
    },
    {
        "title":    "Sankey diagram tras",
        "subtitle": "Diagram toku cen na jednotlivých trasách",
        "href":     "/sankey",
        "accent":   NEON_YELLOW,
        "icon":     "🗺️"
    },
    {
        "title":    "Analyzátor Gini",
        "subtitle": "Analýza nerovnosti rozdělení cen na jednotlivých trasách",
        "href":     "/gini",
        "accent":   NEON_PURPLE,
        "icon":     "📊"
    },
    {
        "title":    "Přehled všech sledovaných tras",
        "subtitle": "Přímé porovnání cen z letišť ve Střední Evropě: PRG / VIE / BUD / BER / WAW ",
        "href":     "/overview",
        "accent":   NEON_YELLOW,
        "icon":     "🗂️"
    },
]

# Karta Manual zobrazená v pravém bočním panelu (symetricky s Traffic Analytics)
MANUAL_PAGE = {
    "title":    "Manuál",
    "subtitle": "Jak používat platformu a interpretovat data",
    "href":     "/info",
    "accent":   NEON_PURPLE,
    "icon":     "📊"
}

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
        "backgroundColor": KPI_BG,
        "border":          f"1px solid {accent}30",
        "borderRadius":    "10px",
        "padding":         "14px 18px",
        "flex":            "1",
        "minWidth":        "120px",
        "boxShadow":       f"0 0 6px {accent}10"
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

    # Hlavička s celkovými ukazateli — vertikální stack (každý KPI na vlastním řádku),
    # aby v úzkém postranním panelu nedocházelo k přetékání.
    def _stat_row(label, value, color):
        return html.Div([
            html.Div(label, style={
                "color":         NEON_BLUE,
                "fontSize":      "9px",
                "letterSpacing": "2px",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "2px"
            }),
            html.Div(f"{value:,}", style={
                "color":      color,
                "fontSize":   "18px",
                "fontWeight": "bold",
                "fontFamily": "Courier New, monospace",
                "textShadow": f"0 0 6px {color}",
                "lineHeight": "1.1"
            })
        ], style={
            "marginBottom":  "10px",
            "textAlign":     "left"
        })

    header_row = html.Div([
        _stat_row("CELKOVÝ POČET NÁVŠTĚV", stats['total'],     NEON_CYAN),
        _stat_row("POSLEDNÍCH 24H",     stats['last_24h'],  NEON_GREEN),
        _stat_row("NOVĚ PŘÍCHOZÍCH ZA 7 DNÍ",    stats['unique_7d'], NEON_PINK),
    ], style={
        "marginBottom":  "12px",
        "paddingBottom": "10px",
        "borderBottom":  f"1px solid {NEON_BLUE}20"
    })





def make_manual_panel():
    """Sestavení pravého bočního panelu s odkazem na manuál.

    Panel je umístěn symetricky proti levému Traffic Analytics panelu.
    Obsahuje krátký nadpis a úzké obdélníkové tlačítko (link), které
    navádí uživatele na detailní stránku /info.
    """
    return html.Div([
        # Hlavička panelu (analogická s "TRAFFIC ANALYTICS" vlevo)
        html.Div("◈  MANUÁL FUNKCÍ APLIKACE", style={
            "color":         NEON_BLUE,
            "fontSize":      "9px",
            "letterSpacing": "3px",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "12px"
        }),

        # Krátký popis pod nadpisem
        html.Div(
            "Jak používat platformu a interpretovat data",
            style={
                "color":         TEXT_MUTED,
                "fontSize":      "10px",
                "lineHeight":    "1.5",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "14px",
                "textAlign":     "left"
            }
        ),

        # Obdélníkové tlačítko (užší forma) — odkaz na manuál
        html.A(
            "▶  OTEVŘÍT MANUÁL",
            href=MANUAL_PAGE["href"],
            style={
                "display":         "block",
                "padding":         "10px 14px",
                "color":           NEON_PURPLE,
                "backgroundColor": KPI_BG,
                "border":          f"1px solid {NEON_PURPLE}80",
                "borderRadius":    "6px",
                "textDecoration":  "none",
                "fontSize":        "11px",
                "letterSpacing":   "2px",
                "textAlign":       "center",
                "fontFamily":      "Courier New, monospace",
                "fontWeight":      "bold",
                "textShadow":      f"0 0 6px {NEON_PURPLE}",
                "boxShadow":       f"0 0 10px {NEON_PURPLE}30"
            }
        ),
    ], style={
        "padding":         "12px 16px",
        "backgroundColor": PANEL_BG,
        "borderRadius":    "10px",
        "border":          f"1px solid {NEON_PURPLE}30",
        "boxShadow":       f"0 0 12px {NEON_PURPLE}15",
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
            html.Span("Aplikace na vizualizaci leteckých dat ", style={
                "color":      NEON_CYAN,
                "fontWeight": "bold",
                "textShadow": f"0 0 6px {NEON_CYAN}"
            }),
            html.Span("by ", style={"color": TEXT_MUTED}),
            html.Span("Matěj Fadrhons ", style={
                "color":      NEON_CYAN,
                "fontWeight": "bold"
            }),
            html.Span(" |  ", style={"color": NEON_BLUE}),
            html.Span("Všechna práva vyhrazena", style={"color": TEXT_MUTED}),
            html.Span("  |  ", style={"color": NEON_BLUE}),
            html.Span("S využítím ", style={"color": TEXT_MUTED}),
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
            html.Span("Data sesbírána na leden 2026  //  Vizualizace slouží výhradně k akademickým a vzdělávacím účelům",
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
                   href="https://github.com/mFadr/NeuralVizualizationApp",
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
    """Sestavení hlavního layoutu, aby se analytiky obnovovaly při každé návštěvě.

    Layout je 3sloupcový a symetrický:
      vlevo:  Traffic Analytics (sledování návštěvnosti)
      střed:  KPI dlaždice + stavová lišta + mřížka 3+3 modulů
      vpravo: Manual for apps functions (přístup k uživatelské příručce)
    """

    # ── Hlavní obsahová oblast (3sloupcová sestava) ──────────────────
    main_content = html.Div([

        # ── Levý sloupec: Traffic Analytics ──────────────────────────
        html.Div([
            make_analytics_panel(),
        ], style={
            "width":     "220px",
            "flexShrink": "0"
        }),

        # ── Střední sloupec: KPI + status + mřížka modulů ────────────
        html.Div([
            # KPI karty — horizontální řada (5 dlaždic)
            html.Div([
                make_kpi_card("VÝCHOZÍ LETIŠTĚ",   KPI["origins"],
                              "letišť",  NEON_CYAN),
                make_kpi_card("CELKOVÝ POČET ZÁZNAMŮ",     f"{KPI['total_records']:,}",
                              "záznamů",     NEON_BLUE),
                make_kpi_card("POČET SLEDOVANÝCH TRAS",    KPI["total_routes"],
                              "linek",   NEON_PURPLE),
                make_kpi_card("PRŮMĚRNÁ CENA LETENKY",  f"${KPI['avg_price']}",
                              "USD",      NEON_YELLOW),
                make_kpi_card("CENOVÝ ROZPTYL",
                              f"${KPI['min_price']}–${KPI['max_price']}",
                              "USD",      NEON_GREEN),
            ], style={
                "display":        "flex",
                "flexWrap":       "wrap",
                "gap":            "12px",
                "marginBottom":   "20px",
                "justifyContent": "center"
            }),

            # Stavová lišta s informacemi o načtených datech
            html.Div([
                html.Div("◈  NAHRANÁ DATA V SYSTÉMU: ", style={
                    "color":         NEON_BLUE,
                    "fontSize":      "9px",
                    "letterSpacing": "3px",
                    "fontFamily":    "Courier New, monospace",
                    "marginBottom":  "8px",
                    "textAlign":     "center"
                }),
                html.Div([
                    html.Span("▶  DATASETY NAHRÁNY  ", style={"color": NEON_CYAN}),
                    html.Span(f"{KPI['origins']}/5 výchozích letišť  ·  ",
                              style={"color": NEON_GREEN}),
                    html.Span(f"{KPI['total_records']:,} celkový počet záznamů  ·  ",
                              style={"color": TEXT_MUTED}),
                    html.Span(f"{KPI['total_routes']} sledovaných tras  ·  ",
                              style={"color": TEXT_MUTED}),
                    html.Span(f"průmerná cena ${KPI['avg_price']}  ·  ",
                              style={"color": NEON_YELLOW}),
                ], style={
                    "fontSize":         "11px",
                    "fontFamily":       "Courier New, monospace",
                    "padding":          "8px 12px",
                    "backgroundColor":  KPI_BG,
                    "borderRadius":     "6px",
                    "border":           f"1px solid {NEON_BLUE}30",
                    "overflowX":        "auto",
                    "whiteSpace":       "nowrap",
                    "textAlign":        "center"
                })
            ], style={
                "marginBottom":     "20px",
                "padding":          "12px 16px",
                "backgroundColor":  PANEL_BG,
                "borderRadius":     "10px",
                "border":           f"1px solid {NEON_BLUE}20",
                "boxShadow":        f"0 0 12px {NEON_BLUE}20"
            }),

            # Mřížka modulů 3 + 3 (dokonale symetrická)
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
                [make_card(p) for p in PAGES[3:6]],
                style={
                    "display":             "grid",
                    "gridTemplateColumns": "1fr 1fr 1fr",
                    "gap":                 "20px",
                    "width":               "100%"
                }
            )
        ], style={
            "flex":      "1",
            "minWidth":  "0"
        }),

        # ── Pravý sloupec: Manual for apps functions ─────────────────
        html.Div([
            make_manual_panel(),
        ], style={
            "width":      "220px",
            "flexShrink": "0"
        }),

    ], style={
        "display":     "flex",
        "gap":         "24px",
        "width":       "100%",
        "alignItems":  "flex-start"
    })

    # ── Sestavení celé stránky ───────────────────────────────────────
    return html.Div([
        html.Div([
            html.H1("APLIKACE: VIZUALIZACE DAT Z VYBRANÝCH LETECKÝCH TRAS", style={
                "color":        NEON_CYAN,
                "textShadow":   f"0 0 20px {NEON_CYAN}",
                "letterSpacing":"5px",
                "fontSize":     "22px",
                "fontFamily":   "Courier New, monospace",
                "margin":       "0 0 18px 0",
                "width":        "100%",
                "textAlign":    "center"
            }),
            html.Div("ANALÝZA 20 VYBRANÝCH LETECKÝCH LINEK Z LETIŠŤ VE STŘEDNÍ EVROPĚ", style={
                "color":         NEON_BLUE,
                "fontSize":      "10px",
                "letterSpacing": "4px",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "32px",
                "textAlign":     "center"
            }),

            main_content

        ], style={
            "maxWidth":  "1280px",
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
        "alignItems":      "stretch",
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

    if pathname == "/overview":
        import vizualizationRoutes
        return vizualizationRoutes.layout, session_data

    if pathname == "/info":
        import vizualizationManual
        return vizualizationManual.layout, session_data

    return build_main_layout(), session_data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)