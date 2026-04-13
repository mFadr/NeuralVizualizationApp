import os
from dash import Dash, html, dcc
import dash

# ── Single shared Dash instance ───────────────────────────────────────
app = Dash(
    __name__,
    use_pages=False,          # we register routes manually
    suppress_callback_exceptions=True
)
server = app.server           # gunicorn entry point

# ── Import all viz modules AFTER app is created ───────────────────────
# Each module registers its own layout on its own route
import vizualizationEmision       # noqa
import vizualizationFlightOffers  # noqa
import vizualizationJanuary       # noqa
import vizualizationSankey        # noqa

# ── Cyberpunk theme colours ───────────────────────────────────────────
BG_COLOR   = "#0b0c10"
PANEL_BG   = "#1f2833"
NEON_CYAN  = "#66fcf1"
NEON_BLUE  = "#45a29e"
NEON_PINK  = "#ff007f"
TEXT_MUTED = "#c5c6c7"

PAGES = [
    {
        "title":       "BOOKING CURVE ANALYZER",
        "subtitle":    "Price trends over the scraping period",
        "href":        "/offers",
        "accent":      NEON_CYAN,
        "icon":        "📈"
    },
    {
        "title":       "JANUARY FLIGHT TRACKER",
        "subtitle":    "Multi-origin price comparison — Jan 2026",
        "href":        "/january",
        "accent":      NEON_PINK,
        "icon":        "✈️"
    },
    {
        "title":       "EMISSION INTELLIGENCE",
        "subtitle":    "CO₂ and per-seat emission analysis",
        "href":        "/emission",
        "accent":      "#39ff14",
        "icon":        "🌍"
    },
    {
        "title":       "ROUTE SANKEY",
        "subtitle":    "Flow diagram of prices between cities",
        "href":        "/sankey",
        "accent":      "#f5c518",
        "icon":        "🗺️"
    },
]

def make_card(page):
    return html.A(
        href=page["href"],
        style={"textDecoration": "none"},
        children=html.Div([
            html.Div(page["icon"], style={
                "fontSize": "32px", "marginBottom": "10px"
            }),
            html.Div(page["title"], style={
                "color": page["accent"],
                "fontSize": "13px",
                "letterSpacing": "2px",
                "fontWeight": "bold",
                "marginBottom": "6px",
                "fontFamily": "Courier New, monospace",
                "textShadow": f"0 0 8px {page['accent']}"
            }),
            html.Div(page["subtitle"], style={
                "color": TEXT_MUTED,
                "fontSize": "11px",
                "fontFamily": "Courier New, monospace"
            })
        ], style={
            "backgroundColor": PANEL_BG,
            "border": f"1px solid {page['accent']}40",
            "borderRadius": "12px",
            "padding": "28px 24px",
            "textAlign": "center",
            "boxShadow": f"0 0 20px {page['accent']}20",
            "transition": "box-shadow 0.2s",
            "cursor": "pointer",
            "minWidth": "220px",
            "flex": "1"
        })
    )

# ── Main page layout ──────────────────────────────────────────────────
main_layout = html.Div([
    html.Div([
        html.H1("✈  FLIGHT ANALYTICS PLATFORM", style={
            "color": NEON_CYAN,
            "textShadow": f"0 0 20px {NEON_CYAN}",
            "letterSpacing": "5px",
            "fontSize": "22px",
            "fontFamily": "Courier New, monospace",
            "margin": "0 0 8px 0"
        }),
        html.Div("CENTRAL OPERATIONS  //  SELECT MODULE", style={
            "color": NEON_BLUE,
            "fontSize": "10px",
            "letterSpacing": "4px",
            "fontFamily": "Courier New, monospace",
            "marginBottom": "48px"
        }),
        html.Div(
            [make_card(p) for p in PAGES],
            style={
                "display": "flex",
                "gap": "24px",
                "flexWrap": "wrap",
                "justifyContent": "center"
            }
        )
    ], style={"textAlign": "center", "maxWidth": "960px", "margin": "0 auto"})
], style={
    "backgroundColor": BG_COLOR,
    "minHeight": "100vh",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "padding": "40px 24px",
    "fontFamily": "Courier New, monospace"
})

# ── URL routing ───────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

@app.callback(
    dash.Output("page-content", "children"),
    dash.Input("url",           "pathname")
)
def route(pathname):
    if pathname == "/offers":
        return vizualizationFlightOffers.layout
    if pathname == "/january":
        return vizualizationJanuary.layout
    if pathname == "/emission":
        return vizualizationEmision.layout
    if pathname == "/sankey":
        return vizualizationSankey.layout
    return main_layout   # default: "/"

# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)