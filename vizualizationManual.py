"""
vizualizationManual.py
Samostatný návod na použití — 6. karta na hlavní stránce.
Popisuje základní kroky pro práci s každou vizualizační aplikací.
"""

from dash import html
from app_instance import app  # noqa

# =====================================================================
# Cyberpunk téma (kopie z main_page.py)
# =====================================================================
BG_COLOR    = "#0b0c10"
PANEL_BG    = "#1f2833"
PANEL_DARK  = "#151c25"
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_PURPLE = "#9d4edd"
NEON_GREEN  = "#39ff14"
NEON_YELLOW = "#f5c518"
NEON_ORANGE = "#ff6600"
TEXT_MUTED  = "#c5c6c7"
TEXT_DIM    = "#6b7280"

# =====================================================================
# Obsah manuálu — každá aplikace jako sekce
# =====================================================================
MANUAL_SECTIONS = [
    {
        "id":      "offers",
        "icon":    "📈",
        "title":   "BOOKING CURVE ANALYZER",
        "accent":  NEON_CYAN,
        "href":    "/offers",
        "popis":   "Sleduje vývoj cen letenek v čase — jak se cena mění v závislosti na tom, "
                   "kolik dní předem je letenka sledována.",
        "kroky": [
            ("výchozí letiště",    "Vyber zdrojové letiště (BER · BUD · PRG · VIE · WAW)."),
            ("destinace",          "Zvol cílovou destinaci nebo ponech 'All' pro všechny trasy."),
            ("letecká společnost", "Filtruj dle konkrétní aerolinky nebo ponech 'All'."),
            ("typ letadla",        "Filtruj dle typu letadla (B738, A320 apod.)."),
            ("režim zobrazení",    "Přepínej mezi daily (každý den sběru dat zvlášť) "
                                   "a monthly (agregace po měsících)."),
            ("agregace",           "V měsíčním režimu zvol průměr nebo medián — "
                                   "oba se zobrazí současně, aktivní je tučný."),
        ],
        "tip": "V denním režimu každá čára = jedno datum odletu. "
               "Čím více čar konverguje doleva, tím stabilnější je cena dané trasy."
    },
    {
        "id":      "january",
        "icon":    "✈️",
        "title":   "JANUARY FLIGHT TRACKER",
        "accent":  NEON_PINK,
        "href":    "/january",
        "popis":   "Multioriginové srovnání cen — porovnává trasy ze dvou různých letišť "
                   "na jednom sloučeném grafu (tracker alfa vs. tracker beta).",
        "kroky": [
            ("agregační metoda",   "Přepínej průměr / medián — platí pro všechny grafy najednou."),
            ("tracker alfa",       "Nastav výchozí letiště, destinaci, leteckou společnost a "
                                   "výběr měsíců pro první trasu (zobrazena azurovou barvou)."),
            ("tracker beta",       "Nastav stejné parametry pro druhou trasu "
                                   "(zobrazena růžovou barvou) — umožňuje přímé srovnání."),
            ("filtry destinací",   "Ve spodních grafech (nejlevnější / nejdražší trasy / "
                                   "srovnání letišť) zaškrtni, které destinace chceš zahrnout."),
        ],
        "tip": "Nastav tracker alfa na PRG→AMS a tracker beta na WAW→AMS pro přímé srovnání "
               "cen ze dvou sousedních letišť na stejné trase."
    },
    {
        "id":      "emission",
        "icon":    "🌍",
        "title":   "EMISSION INTELLIGENCE",
        "accent":  NEON_GREEN,
        "href":    "/emission",
        "popis":   "Analyzuje uhlíkovou stopu letů — srovnává emise CO₂ dle aerolinky, "
                   "typu letadla nebo trasy.",
        "kroky": [
            ("výchozí letiště",    "Vyber zdrojové letiště."),
            ("destinace",          "Vyber cílovou destinaci nebo 'All'."),
            ("letecká společnost", "Filtruj dle aerolinky."),
            ("režim emisí",        "Přepínej mezi třemi metrikami:\n"
                                   "• AVG CO₂ (kg/hod) — průměrná emise motoru za hodinu\n"
                                   "• Est. CO₂ (kg/let) — celková emise za jeden let\n"
                                   "• Emise/sedadlo (kg/hod) — emise na jedno sedadlo"),
            ("seskupit podle",     "Seskup čáry dle letecké společnosti, typu letadla nebo trasy "
                                   "pro různé úhly pohledu."),
        ],
        "tip": "Emise/sedadlo je nejférovější metrika pro srovnání letadel různé velikosti — "
               "velké letadlo může mít vyšší celkové emise, ale nižší na pasažéra."
    },
    {
        "id":      "sankey",
        "icon":    "🗺️",
        "title":   "ROUTE SANKEY DIAGRAM",
        "accent":  NEON_YELLOW,
        "href":    "/sankey",
        "popis":   "Vizualizuje průměrné nebo mediánové ceny jako tok (flow) "
                   "mezi zdrojovými a cílovými letišti.",
        "kroky": [
            ("výchozí letiště",   "Vyber konkrétní zdrojové letiště nebo 'All Origins' "
                                  "pro zobrazení všech toků najednou."),
            ("destinace",         "Filtruj dle cílové destinace."),
            ("cenová statistika", "Přepínej průměr vs. medián — "
                                  "průměr = azurová, medián = růžová barva toků."),
        ],
        "tip": "Šířka toku odpovídá výši ceny — čím širší tok, tím dražší trasa. "
               "Ve statistické liště pod filtry vidíš rozdíl (Δ) mezi průměrem a mediánem "
               "pro každou trasu."
    },
    {
        "id":      "gini",
        "icon":    "📊",
        "title":   "GINI ANALYZER",
        "accent":  NEON_PURPLE,
        "href":    "/gini",
        "popis":   "Měří cenovou nerovnoměrnost pomocí True Gini koeficientu "
                   "(Santos & Dias, 2024) — čím vyšší hodnota, tím větší rozptyl cen.",
        "kroky": [
            ("výchozí letiště", "Filtruj dle zdrojového letiště nebo zobraz všechna najednou."),
            ("destinace",       "Filtruj dle destinace."),
            ("režim grafu",     "Přepínej mezi:\n"
                                "• Bar — horizontální sloupcový graf, seřazený dle Giniho koeficientu\n"
                                "• Heatmap — matice výchozí letiště × destinace, barva = míra nerovnoměrnosti"),
        ],
        "interpretace": [
            ("< 0,2",    "Velmi nízká nerovnoměrnost — ceny jsou stabilní"),
            ("0,2–0,3",  "Nízká nerovnoměrnost"),
            ("0,3–0,4",  "Střední nerovnoměrnost — typické pro sezónní výkyvy"),
            ("0,4–0,5",  "Vysoká nerovnoměrnost — ceny silně kolísají"),
            ("> 0,5",    "Velmi vysoká nerovnoměrnost — výrazná cenová variabilita"),
        ],
        "tip": "True Gini splňuje symetrii, škálovou invarianci a Pigou-Daltonův princip, "
               "ale nesplňuje princip populace — nelze jej použít pro srovnání skupin "
               "různé velikosti."
    },
]

# =====================================================================
# Přehled kódů letišť — pro orientaci v ostatních modulech
# =====================================================================
ORIGIN_AIRPORTS = [
    ("BER", "Berlín"),
    ("WAW", "Varšava"),
    ("PRG", "Praha"),
    ("VIE", "Vídeň"),
    ("BUD", "Budapešť"),
]

DESTINATION_AIRPORTS = [
    ("FCO", "Řím"),
    ("BCN", "Barcelona"),
    ("LON", "Londýn (všechna letiště)"),
    ("AMS", "Amsterdam"),
]


def _airport_row(code: str, city: str, accent: str):
    """Jeden řádek tabulky letišť — kód + město."""
    return html.Div([
        html.Span(code, style={
            "color":         accent,
            "fontWeight":    "bold",
            "fontSize":      "11px",
            "letterSpacing": "1px",
            "minWidth":      "48px",
            "display":       "inline-block",
            "fontFamily":    "Courier New, monospace",
            "textShadow":    f"0 0 4px {accent}"
        }),
        html.Span("·", style={
            "color":      TEXT_DIM,
            "marginLeft": "6px",
            "marginRight":"10px",
            "fontSize":   "11px"
        }),
        html.Span(city, style={
            "color":      TEXT_MUTED,
            "fontSize":   "11px",
            "fontFamily": "Courier New, monospace"
        })
    ], style={
        "display":       "flex",
        "alignItems":    "center",
        "padding":       "5px 0",
        "borderBottom":  f"1px solid {accent}10"
    })


def _airport_overview_table():
    """Tabulka s přehledem kódů zdrojových letišť a destinací (dva sloupce vedle sebe)."""

    # Levý sloupec — Výchozí letiště
    origin_col = html.Div([
        html.Div("výchozí letiště", style={
            "color":         NEON_CYAN,
            "fontSize":      "10px",
            "letterSpacing": "3px",
            "fontWeight":    "bold",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "8px",
            "paddingBottom": "6px",
            "borderBottom":  f"1px solid {NEON_CYAN}40",
            "textShadow":    f"0 0 6px {NEON_CYAN}",
            "textTransform": "uppercase"
        }),
        html.Div(
            [_airport_row(code, city, NEON_CYAN) for code, city in ORIGIN_AIRPORTS]
        )
    ], style={"flex": "1", "minWidth": "0"})

    # Pravý sloupec — Destinace
    dest_col = html.Div([
        html.Div("destinace", style={
            "color":         NEON_PINK,
            "fontSize":      "10px",
            "letterSpacing": "3px",
            "fontWeight":    "bold",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "8px",
            "paddingBottom": "6px",
            "borderBottom":  f"1px solid {NEON_PINK}40",
            "textShadow":    f"0 0 6px {NEON_PINK}",
            "textTransform": "uppercase"
        }),
        html.Div(
            [_airport_row(code, city, NEON_PINK) for code, city in DESTINATION_AIRPORTS]
        )
    ], style={"flex": "1", "minWidth": "0"})

    # Hlavička tabulky + dva sloupce vedle sebe
    return html.Div([
        html.Div("◈  PŘEHLED LETIŠŤ  //  KÓD A MĚSTO", style={
            "color":         NEON_BLUE,
            "fontSize":      "9px",
            "letterSpacing": "3px",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "12px",
            "textAlign":     "center"
        }),
        html.Div(
            [origin_col, dest_col],
            style={
                "display":  "flex",
                "gap":      "32px",
                "alignItems": "flex-start"
            }
        )
    ], style={
        "backgroundColor": PANEL_BG,
        "border":          f"1px solid {NEON_BLUE}30",
        "borderRadius":    "10px",
        "padding":         "16px 22px",
        "marginBottom":    "24px",
        "boxShadow":       f"0 0 12px {NEON_BLUE}15"
    })

# =====================================================================
# Pomocné komponenty
# =====================================================================
def _step_row(label: str, text: str, accent: str):
    lines = text.split("\n")
    content = [html.Span(lines[0], style={"color": TEXT_MUTED})]
    for line in lines[1:]:
        content.append(html.Br())
        content.append(html.Span(line, style={"color": TEXT_DIM, "paddingLeft": "12px"}))
    return html.Div([
        html.Span(label, style={
            "color":          accent,
            "fontWeight":     "bold",
            "fontSize":       "10px",
            "letterSpacing":  "1px",
            "minWidth":       "180px",
            "display":        "inline-block",
            "fontFamily":     "Courier New, monospace"
        }),
        html.Span(content, style={
            "fontSize":   "12px",
            "fontFamily": "Courier New, monospace",
            "lineHeight": "1.6"
        })
    ], style={
        "display":       "flex",
        "gap":           "12px",
        "padding":       "7px 0",
        "borderBottom":  f"1px solid {accent}15",
        "alignItems":    "flex-start"
    })


def _interp_row(range_str: str, desc: str):
    return html.Div([
        html.Span(range_str, style={
            "color":      NEON_PURPLE,
            "fontWeight": "bold",
            "fontSize":   "11px",
            "minWidth":   "70px",
            "display":    "inline-block",
            "fontFamily": "Courier New, monospace"
        }),
        html.Span(desc, style={
            "color":      TEXT_MUTED,
            "fontSize":   "11px",
            "fontFamily": "Courier New, monospace"
        })
    ], style={"display": "flex", "gap": "10px", "padding": "4px 0"})


def _section(sec: dict) -> html.Div:
    accent = sec["accent"]

    header = html.Div([
        html.Span(sec["icon"], style={"fontSize": "22px", "marginRight": "10px"}),
        html.A(
            sec["title"],
            href=sec["href"],
            style={
                "color":          accent,
                "fontSize":       "14px",
                "fontWeight":     "bold",
                "letterSpacing":  "2px",
                "fontFamily":     "Courier New, monospace",
                "textShadow":     f"0 0 8px {accent}",
                "textDecoration": "none"
            }
        ),
        html.Span(" ↗", style={"color": accent, "fontSize": "11px"})
    ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"})

    desc = html.P(sec["popis"], style={
        "color":        TEXT_MUTED,
        "fontSize":     "12px",
        "fontFamily":   "Courier New, monospace",
        "marginBottom": "12px",
        "lineHeight":   "1.6",
        "borderLeft":   f"2px solid {accent}40",
        "paddingLeft":  "10px"
    })

    steps_label = html.Div("kroky", style={
        "color":         NEON_BLUE,
        "fontSize":      "9px",
        "letterSpacing": "3px",
        "fontFamily":    "Courier New, monospace",
        "marginBottom":  "6px",
        "textTransform": "uppercase"
    })

    steps = html.Div(
        [_step_row(lbl, txt, accent) for lbl, txt in sec["kroky"]],
        style={"marginBottom": "12px"}
    )

    children = [header, desc, steps_label, steps]

    # Interpretační tabulka (pouze Gini)
    if "interpretace" in sec:
        interp_label = html.Div("interpretace", style={
            "color":         NEON_BLUE,
            "fontSize":      "9px",
            "letterSpacing": "3px",
            "fontFamily":    "Courier New, monospace",
            "marginBottom":  "6px",
            "textTransform": "uppercase"
        })
        interp_rows = html.Div(
            [_interp_row(r, d) for r, d in sec["interpretace"]],
            style={
                "backgroundColor": PANEL_DARK,
                "borderRadius":    "6px",
                "padding":         "8px 12px",
                "marginBottom":    "12px"
            }
        )
        children += [interp_label, interp_rows]

    # Tip
    tip = html.Div([
        html.Span("💡 tip  ", style={
            "color":      NEON_YELLOW,
            "fontSize":   "10px",
            "fontWeight": "bold",
            "fontFamily": "Courier New, monospace",
            "textTransform": "uppercase"
        }),
        html.Span(sec["tip"], style={
            "color":      TEXT_DIM,
            "fontSize":   "11px",
            "fontFamily": "Courier New, monospace",
            "lineHeight": "1.5"
        })
    ], style={
        "backgroundColor": PANEL_DARK,
        "borderRadius":    "6px",
        "padding":         "8px 12px",
        "border":          f"1px solid {NEON_YELLOW}20"
    })
    children.append(tip)

    return html.Div(children, style={
        "backgroundColor": PANEL_BG,
        "border":          f"1px solid {accent}25",
        "borderRadius":    "12px",
        "padding":         "20px",
        "boxShadow":       f"0 0 16px {accent}10"
    })


# =====================================================================
# Rozložení
# =====================================================================
layout = html.Div([

    # ── Tlačítko zpět ──────────────────────────────────────────────────
    html.A("← ZPĚT NA HLAVNÍ STRÁNKU", href="/", style={
        "display":        "inline-block",
        "color":          NEON_CYAN,
        "border":         f"1px solid {NEON_BLUE}",
        "padding":        "6px 16px",
        "borderRadius":   "6px",
        "textDecoration": "none",
        "fontSize":       "11px",
        "letterSpacing":  "2px",
        "marginBottom":   "20px",
        "fontFamily":     "Courier New, monospace",
        "backgroundColor": PANEL_BG
    }),

    # ── Nadpis ────────────────────────────────────────────────────────
    html.Div([
        html.H2("◈  NÁVOD NA POUŽITÍ", style={
            "color":         NEON_CYAN,
            "textShadow":    f"0 0 16px {NEON_CYAN}",
            "letterSpacing": "5px",
            "fontSize":      "18px",
            "fontFamily":    "Courier New, monospace",
            "margin":        "0 0 4px 0",
            "textAlign":     "center"
        }),
        html.Div(
            "FLIGHT ANALYTICS PLATFORM  ·  UŽIVATELSKÝ MANUÁL  ·  v1.0",
            style={
                "color":         NEON_BLUE,
                "fontSize":      "9px",
                "letterSpacing": "3px",
                "fontFamily":    "Courier New, monospace",
                "textAlign":     "center",
                "marginBottom":  "28px"
            }
        )
    ]),

    # ── Přehled letišť (tabulka kód → město) ──────────────────────────
    _airport_overview_table(),

    # ── Úvod ──────────────────────────────────────────────────────────
    html.Div([
        html.Span("ℹ️  ", style={"fontSize": "14px"}),
        html.Span(
            "Platforma obsahuje 5 analytických modulů. Každý modul je přístupný "
            "přes kartu na hlavní stránce nebo přes navigační odkaz v záhlaví každé "
            "vizualizace. Klikni na název modulu v manuálu pro přímé přesměrování.",
            style={
                "color":      TEXT_MUTED,
                "fontSize":   "12px",
                "fontFamily": "Courier New, monospace",
                "lineHeight": "1.6"
            }
        )
    ], style={
        "backgroundColor": PANEL_BG,
        "border":          f"1px solid {NEON_BLUE}30",
        "borderRadius":    "10px",
        "padding":         "14px 18px",
        "marginBottom":    "24px"
    }),

    # ── Sekce aplikací ────────────────────────────────────────────────
    html.Div([
        # Levý sloupec: Offers, Emission, Gini
        html.Div(
            [_section(s) for s in MANUAL_SECTIONS if s["id"] in ("offers", "emission", "gini")],
            style={"display": "flex", "flexDirection": "column", "gap": "20px", "flex": "1"}
        ),
        # Pravý sloupec: January, Sankey
        html.Div(
            [_section(s) for s in MANUAL_SECTIONS if s["id"] in ("january", "sankey")],
            style={"display": "flex", "flexDirection": "column", "gap": "20px", "flex": "1"}
        ),
    ], style={
        "display": "flex",
        "gap":     "20px",
        "alignItems": "flex-start"
    }),

    # ── Patička ───────────────────────────────────────────────────────
    html.Div([
        html.Span("Reference: ", style={"color": NEON_BLUE}),
        html.Span(
            "Santos & Dias (2024) — True Gini Coefficient, "
            "Acta Scientiarum Technology, v.46, e64563  ·  "
            "Bowles & Carlin (2020) — Economics Letters, 186, 108789",
            style={"color": TEXT_DIM}
        )
    ], style={
        "marginTop":  "28px",
        "padding":    "12px 16px",
        "borderTop":  f"1px solid {NEON_BLUE}20",
        "fontSize":   "10px",
        "fontFamily": "Courier New, monospace"
    })

], style={
    "backgroundColor": BG_COLOR,
    "color":           NEON_CYAN,
    "padding":         "20px 28px",
    "fontFamily":      "Courier New, monospace",
    "minHeight":       "100vh",
    "boxSizing":       "border-box"
})


# =====================================================================
# Vstupní bod (jen pro lokální vývoj)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8056))
    app.run(host="0.0.0.0", port=port, debug=False)
