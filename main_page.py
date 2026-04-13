from dash import Dash, html

# =====================================================================
# Theme Configuration (Cyberpunk Style)
# =====================================================================
BG_COLOR = "#0b0c10"        # Deep void black
PANEL_BG = "#1f2833"        # Dark gray for panels
NEON_CYAN = "#66fcf1"       # Primary text/accents
NEON_BLUE = "#45a29e"       # Secondary accents
NEON_PINK = "#ff007f"       # Contrast color
TEXT_MUTED = "#c5c6c7"      # Muted text

app = Dash(__name__)
server = app.server

# =====================================================================
# Main Layout
# =====================================================================
app.layout = html.Div([

    # 🌟 MAIN TITLE
    html.H1(
        "✈️ FLIGHT PRICES VIZUALIZATION",
        style={
            "textAlign": "center",
            "color": NEON_CYAN,
            "textShadow": f"0 0 15px {NEON_CYAN}",
            "letterSpacing": "4px",
            "paddingTop": "40px",
            "paddingBottom": "40px",
            "margin": "0"
        }
    ),

    # 🪟 3 HORIZONTAL WINDOWS CONTAINER
    html.Div([

        # --- WINDOW 1: The Finished App (chartActive) ---
        html.Div([
            html.H3("MODULE 1: ACTIVE TRACKER", style={"color": NEON_CYAN, "textAlign": "center", "marginTop": "10px"}),

            # The Iframe "looks" at port 8050 where your chartActive script is running
            html.Iframe(
                src="http://localhost:8050",
                style={
                    "width": "100%",
                    "height": "800px",
                    "border": "none",
                    "borderRadius": "10px"
                }
            )
        ], style={
            "flex": "1", # Makes it take up 1/3 of the space
            "backgroundColor": PANEL_BG,
            "borderRadius": "15px",
            "padding": "15px",
            "boxShadow": f"0 0 20px {NEON_CYAN}40",
            "border": f"1px solid {NEON_BLUE}"
        }),

        # --- WINDOW 2: Future App ---
        html.Div([
            html.H3("MODULE 2: PREDICTIVE AI", style={"color": NEON_PINK, "textAlign": "center", "marginTop": "10px"}),
            html.Div(
                "SYSTEM OFFLINE / AWAITING DEPLOYMENT",
                style={
                    "color": TEXT_MUTED,
                    "textAlign": "center",
                    "marginTop": "350px",
                    "fontStyle": "italic"
                }
            )
        ], style={
            "flex": "1", # Makes it take up 1/3 of the space
            "backgroundColor": PANEL_BG,
            "borderRadius": "15px",
            "padding": "15px",
            "boxShadow": f"0 0 20px {NEON_PINK}40",
            "border": f"1px solid #7209B7"
        }),

        # --- WINDOW 3: Future App ---
        html.Div([
            html.H3("MODULE 3: ROUTE OPTIMIZATION", style={"color": "#9D4EDD", "textAlign": "center", "marginTop": "10px"}),
            html.Div(
                "SYSTEM OFFLINE / AWAITING DEPLOYMENT",
                style={
                    "color": TEXT_MUTED,
                    "textAlign": "center",
                    "marginTop": "350px",
                    "fontStyle": "italic"
                }
            )
        ], style={
            "flex": "1", # Makes it take up 1/3 of the space
            "backgroundColor": PANEL_BG,
            "borderRadius": "15px",
            "padding": "15px",
            "boxShadow": f"0 0 20px #9D4EDD40",
            "border": f"1px solid #9D4EDD"
        }),
        # --- WINDOW 3: Emision App ---
        html.Div([
            html.H4("MODULE 4: EMISION", style={"color": "#9D4EDD", "textAlign": "center", "marginTop": "10px"}),
            html.Div(
                "SYSTEM OFFLINE / AWAITING DEPLOYMENT",
                style={
                    "color": TEXT_MUTED,
                    "textAlign": "center",
                    "marginTop": "350px",
                    "fontStyle": "italic"
                }
            )
        ], style={
            "flex": "1", # Makes it take up 1/3 of the space
            "backgroundColor": PANEL_BG,
            "borderRadius": "15px",
            "padding": "15px",
            "boxShadow": f"0 0 20px #9D4EDD40",
            "border": f"1px solid #9D4EDD"
        })

    ], style={
        "display": "flex",          # This enables the horizontal layout
        "flexDirection": "row",     # Places items side-by-side
        "gap": "30px",              # Space between the windows
        "padding": "0 40px",        # Margin on the far left and right of the screen
        "height": "850px"
    })

], style={
    "backgroundColor": BG_COLOR,
    "minHeight": "100vh",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "overflowX": "hidden"
})

if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False        # never run debug=True in production
    )