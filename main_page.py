import os
from dash import html, dcc, Input, Output
from app_instance import app, server   # noqa — server exported for gunicorn

# =====================================================================
# Cyberpunk theme
# =====================================================================
BG_COLOR   = "#0b0c10"
PANEL_BG   = "#1f2833"
NEON_CYAN  = "#66fcf1"
NEON_BLUE  = "#45a29e"
NEON_PINK  = "#ff007f"
TEXT_MUTED = "#c5c6c7"

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
]

# =====================================================================
# Main page layout (landing page)
# =====================================================================
def make_card(page):
    return html.A(
        href=page["href"],
        style={"textDecoration": "none", "display": "block", "height": "100%"},
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
            "padding": "40px 32px",
            "textAlign": "center",
            "boxShadow": f"0 0 20px {page['accent']}20",
            "cursor": "pointer",
            "height": "100%",
            "boxSizing": "border-box"
        })
    )


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
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gridTemplateRows":    "1fr 1fr",
                "gap": "24px",
                "width": "100%"
            }
        )
    ], style={"textAlign": "center", "maxWidth": "780px", "margin": "0 auto", "width": "100%"})
], style={
    "backgroundColor": BG_COLOR,
    "minHeight": "100vh",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "padding": "40px 24px",
    "fontFamily": "Courier New, monospace"
})

# =====================================================================
# Root layout — URL router
# =====================================================================
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# =====================================================================
# Routing callback — LAZY imports inside the function
# This is the key fix: viz modules are imported only when first needed,
# not at startup, which breaks the circular import completely.
# =====================================================================
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

    return main_layout


# =====================================================================
# Entry point (local dev only — production uses gunicorn)
# =====================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)