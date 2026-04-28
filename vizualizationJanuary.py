import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from app_instance import app
from config import DATASET_PATHS
# =====================================================================
# 1️⃣ Function: Load CSV data from file
# =====================================================================
def load_data_from_file(file_path):
    df = pd.read_csv(file_path, sep=r"[\t;,]", engine="python")

    # Clean price
    df["price"] = df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)

    # Ensure expected columns exist
    for col in ["departure_time", "duration", "Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col not in df.columns:
            df[col] = None

    # Convert departure_time
    if "departure_time" in df.columns and df["departure_time"].notna().any():
        def normalize_time(time_str):
            if pd.isna(time_str):
                return time_str
            time_str = str(time_str).strip()
            if "AM" in time_str.upper() or "PM" in time_str.upper():
                try:
                    parsed_time = pd.to_datetime(time_str, format="%I:%M %p", errors="coerce")
                    if pd.notna(parsed_time):
                        return parsed_time.strftime("%H:%M")
                except:
                    pass
            return time_str

        df["departure_time"] = df["departure_time"].apply(normalize_time)

    # Convert to datetime
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df["search_date"] = pd.to_datetime(df["search_date"], errors="coerce")

    # Clean airline name
    df["airline"] = df["airline_details"].astype(str).str.strip()

    # Parse CO2 data - handle various formats
    for col in ["Est. CO2 (kg)", "AVG CO2 (kg/hr)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    # Rename columns
    df.rename(
        columns={
            "flight_date": "Date",
            "origin": "Origin",
            "destination": "Destination",
            "price": "Price",
            "airline": "Airline",
            "departure_time": "DepartureTime",
            "duration": "Duration",
            "Est. CO2 (kg)": "EstCO2",
            "AVG CO2 (kg/hr)": "AvgCO2"
        },
        inplace=True,
    )

    return df

# =====================================================================
# 2️⃣ Theme Configuration (Cyberpunk Style)
# =====================================================================
# Color Palette
BG_COLOR = "#0b0c10"        # Deep void black
GWHITE = "#F8F8FF"             # Light gray for text and gridlines
PANEL_BG = "#1f2833"        # Dark gray for panels
NEON_CYAN = "#66fcf1"       # Primary text/accents
NEON_BLUE = "#45a29e"       # Secondary accents
NEON_PINK = "#ff007f"       # Contrast color for charts
TEXT_MUTED = "#c5c6c7"      # Muted text
DROPDOWN_STYLE = {"color": "black", "marginBottom": "15px"} # Dropdowns need dark text to be readable without complex CSS

# New colors for horizontal bar charts
TRUE_PURPLE = "#9D4EDD"      # 1st chart
ELECTRIC_PURPLE = "#7209B7"  # 2nd chart
CHART_CYAN = "#00D9FF"       # 3rd chart

# Shared height so filter panel and main chart end on the same bottom line
MAIN_PANEL_HEIGHT = "760px"

# =====================================================================
# 3️⃣ Layout
# =====================================================================

# ── Back button ──────────────────────────────────────────────────────
_back_btn = html.A(
    "← BACK TO MAIN",
    href="/",
    style={
        "display":        "inline-block",
        "color":          NEON_CYAN,
        "border":         f"1px solid {NEON_BLUE}",
        "padding":        "6px 16px",
        "borderRadius":   "6px",
        "textDecoration": "none",
        "fontSize":       "11px",
        "letterSpacing":  "2px",
        "marginBottom":   "14px",
        "fontFamily":     "Courier New, monospace",
        "backgroundColor": PANEL_BG
    }
)

layout = html.Div([_back_btn,
                   html.H2(
                       "✈️ NEURAL FLIGHT TRACKER v2.0 - MULTI-ORIGIN",
                       style={
                           "textAlign": "center",
                           "textShadow": f"0 0 10px {NEON_CYAN}",
                           "letterSpacing": "3px",
                           "marginBottom": "30px"
                       }
                   ),

                   # Main Container
                   html.Div([

                       # 🎛️ LEFT PANEL: Filters
                       html.Div([
                           html.H3("SYSTEM PARAMETERS", style={"color": NEON_BLUE, "borderBottom": f"1px solid {NEON_BLUE}", "paddingBottom": "10px"}),

                           # Aggregation Method Toggle
                           html.Div([
                               html.Label("Aggregation Method", style={"color": TEXT_MUTED, "fontSize": "12px"}),
                               dcc.RadioItems(
                                   id="agg-method",
                                   options=[
                                       {"label": "  Mean",   "value": "mean"},
                                       {"label": "  Median", "value": "median"}
                                   ],
                                   value="mean",
                                   labelStyle={"display": "inline-block", "color": NEON_CYAN, "marginRight": "16px", "fontSize": "13px"},
                                   style={"marginTop": "6px", "marginBottom": "16px"}
                               )
                           ], style={"borderBottom": f"1px solid {NEON_BLUE}40", "paddingBottom": "12px", "marginBottom": "8px"}),

                           # Filters Chart 1
                           html.Div([
                               html.H4("TRACKER ALPHA", style={"color": NEON_CYAN, "marginTop": "20px"}),
                               html.Label("Dataset Origin"),
                               dcc.Dropdown(
                                   id="dataset-origin-1",
                                   options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                                   value="PRG",
                                   style=DROPDOWN_STYLE
                               ),
                               html.Label("Destination"),
                               dcc.Dropdown(id="destination-filter-1", value="AMS", style=DROPDOWN_STYLE),
                               html.Label("Airline"),
                               dcc.Dropdown(id="airline-filter-1", value="All", style=DROPDOWN_STYLE),
                               html.Label("Search Date"),
                               dcc.Dropdown(id="search-date-filter-1", value="All", style=DROPDOWN_STYLE)
                           ], style={"border": f"1px solid {NEON_CYAN}", "padding": "15px", "borderRadius": "10px", "marginBottom": "20px", "boxShadow": f"0 0 10px {NEON_CYAN}40"}),

                           # Filters Chart 2
                           html.Div([
                               html.H4("TRACKER BETA", style={"color": NEON_PINK}),
                               html.Label("Dataset Origin"),
                               dcc.Dropdown(
                                   id="dataset-origin-2",
                                   options=['BER', 'BUD', 'PRG', 'VIE', 'WAW'],
                                   value="PRG",
                                   style=DROPDOWN_STYLE
                               ),
                               html.Label("Destination"),
                               dcc.Dropdown(id="destination-filter-2", value="FCO", style=DROPDOWN_STYLE),
                               html.Label("Airline"),
                               dcc.Dropdown(id="airline-filter-2", value="All", style=DROPDOWN_STYLE),
                               html.Label("Search Date"),
                               dcc.Dropdown(id="search-date-filter-2", value="All", style=DROPDOWN_STYLE)
                           ], style={"border": f"1px solid {NEON_PINK}", "padding": "15px", "borderRadius": "10px", "boxShadow": f"0 0 10px {NEON_PINK}40"})

                       ], style={
                           "width": "25%",
                           "backgroundColor": PANEL_BG,
                           "padding": "20px",
                           "borderRadius": "15px",
                           "boxShadow": f"0 0 20px {NEON_BLUE}60",
                           "height": MAIN_PANEL_HEIGHT,
                           "overflowY": "auto"
                       }),

                       # 📈 RIGHT PANEL: Charts
                       html.Div([

                           # Merged Chart Container - Both trackers on same chart
                           html.Div([
                               dcc.Graph(
                                   id="merged-price-chart",
                                   style={"height": "100%"},
                                   config={"responsive": True}
                               )
                           ], style={"height": MAIN_PANEL_HEIGHT, "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {NEON_CYAN}80", "marginBottom": "30px"}),



                       ], style={"width": "75%", "display": "flex", "flexDirection": "column"})

                   ], style={"display": "flex", "gap": "30px"}),

                   # 📊 BOTTOM HORIZONTAL BAR CHARTS (3 in one line)
                   html.Div([
                       # Chart 3: 10 Cheapest Routes
                       html.Div([
                           html.Div([
                               html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                               dcc.Checklist(
                                   id="destination-checklist-cheapest",
                                   options=[
                                       {'label': ' AMS', 'value': 'AMS'},
                                       {'label': ' BCN', 'value': 'BCN'},
                                       {'label': ' FCO', 'value': 'FCO'},
                                       {'label': ' LON', 'value': 'LON'}
                                   ],
                                   value=['AMS', 'BCN', 'FCO', 'LON'],
                                   inline=True,
                                   labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                               ),
                           ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
                           dcc.Graph(id="cheapest-routes-chart")
                       ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {TRUE_PURPLE}80"}),

                       # Chart 4: 10 Most Expensive Routes
                       html.Div([
                           html.Div([
                               html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                               dcc.Checklist(
                                   id="destination-checklist-expensive",
                                   options=[
                                       {'label': ' AMS', 'value': 'AMS'},
                                       {'label': ' BCN', 'value': 'BCN'},
                                       {'label': ' FCO', 'value': 'FCO'},
                                       {'label': ' LON', 'value': 'LON'}
                                   ],
                                   value=['AMS', 'BCN', 'FCO', 'LON'],
                                   inline=True,
                                   labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                               ),
                           ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
                           dcc.Graph(id="expensive-routes-chart")
                       ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {ELECTRIC_PURPLE}80"}),

                       # Chart 5: Origin Airport Comparison with filters
                       html.Div([
                           html.Div([
                               html.Label("Destination Filters:", style={"color": NEON_CYAN, "marginBottom": "10px"}),
                               dcc.Checklist(
                                   id="destination-checklist",
                                   options=[
                                       {'label': ' AMS', 'value': 'AMS'},
                                       {'label': ' BCN', 'value': 'BCN'},
                                       {'label': ' FCO', 'value': 'FCO'},
                                       {'label': ' LON', 'value': 'LON'}
                                   ],
                                   value=['AMS', 'BCN', 'FCO', 'LON'],
                                   inline=True,
                                   labelStyle={"color": "white", "display": "inline-flex", "alignItems": "center", "marginRight": "15px"}
                               ),
                           ], style={"backgroundColor": "#333333", "padding": "10px", "borderRadius": "10px", "marginBottom": "10px"}),
                           dcc.Graph(id="origin-comparison-chart")
                       ], style={"flex": "1", "borderRadius": "15px", "overflow": "hidden", "boxShadow": f"0 0 15px {CHART_CYAN}80"})

                   ], style={"display": "flex", "gap": "20px", "marginTop": "30px"})

                   ], style={
    "backgroundColor": BG_COLOR,
    "color": NEON_CYAN,
    "minHeight": "100vh",
    "padding": "30px",
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
})

# =====================================================================
# 4️⃣ Callbacks & Chart Styling
# =====================================================================
# Define allowed airlines mapping (IATA code to full name)
ALLOWED_AIRLINES = {
    'BA': 'British Airways',
    'FR': 'Ryanair',
    'KL': 'KLM',
    'LO': 'LOT',
    'OS': 'Austrian Airlines',
    'QS': 'Smartwings',
    'RK': 'Ryanair UK',
    'U2': 'EasyJet',
    'VY': 'Vueling',
    'W4': 'Wizz Air',
    'W6': 'Wizz Air',
    'W9': 'Wizz Air'
}

def filter_allowed_airlines(available_airlines):
    """Filter airlines to only include those in the ALLOWED_AIRLINES list"""
    filtered = []
    for airline in available_airlines:
        if pd.isna(airline):
            continue
        airline = str(airline).strip()
        if not airline:
            continue
        # Check if airline matches any code or full name in ALLOWED_AIRLINES
        airline_upper = airline.upper()
        if airline in ALLOWED_AIRLINES or airline in ALLOWED_AIRLINES.values():
            filtered.append(airline)
        # Also check if airline contains the code or name
        elif any(code in airline_upper for code in ALLOWED_AIRLINES.keys()):
            filtered.append(airline)
        elif any(name.upper() in airline_upper for name in ALLOWED_AIRLINES.values()):
            filtered.append(airline)
    return filtered

def clean_sorted_unique(series):
    """Return a stable, case-insensitive sorted list of non-empty string values."""
    cleaned = (
        series.dropna()
        .astype("string")
        .str.strip()
    )
    cleaned = cleaned[cleaned.ne("")]
    return sorted(cleaned.unique().tolist(), key=str.casefold)

# Callback to update destination options when dataset origin changes (Chart 1)
@app.callback(
    Output("destination-filter-1", "options"),
    Output("destination-filter-1", "value"),
    Input("dataset-origin-1", "value")
)
def update_destinations_1(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback to update destination options when dataset origin changes (Chart 2)
@app.callback(
    Output("destination-filter-2", "options"),
    Output("destination-filter-2", "value"),
    Input("dataset-origin-2", "value")
)
def update_destinations_2(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]
    destinations = ["All"] + clean_sorted_unique(df["Destination"])
    default_value = destinations[1] if len(destinations) > 1 else "All"
    return destinations, default_value

# Callback to update airline options (Chart 1)
@app.callback(
    Output("airline-filter-1", "options"),
    Output("airline-filter-1", "value"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value")
)
def update_airline_options_1(selected_dataset_origin, selected_destination):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = datasets[selected_dataset_origin].copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Get unique airlines for this route
    available_airlines = filtered["Airline"].unique().tolist()

    # Filter to only allowed airlines
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback to update airline options (Chart 2)
@app.callback(
    Output("airline-filter-2", "options"),
    Output("airline-filter-2", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value")
)
def update_airline_options_2(selected_dataset_origin, selected_destination):
    if selected_dataset_origin not in datasets:
        return [], None

    filtered = datasets[selected_dataset_origin].copy()
    if selected_destination != "All":
        filtered = filtered[filtered["Destination"] == selected_destination]

    # Get unique airlines for this route
    available_airlines = filtered["Airline"].unique().tolist()

    # Filter to only allowed airlines
    allowed_route_airlines = filter_allowed_airlines(available_airlines)

    airlines = ["All"] + sorted(allowed_route_airlines)
    return airlines, "All"

# Callback to update search date options (Chart 1)
@app.callback(
    Output("search-date-filter-1", "options"),
    Output("search-date-filter-1", "value"),
    Input("dataset-origin-1", "value")
)
def update_search_dates_1(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]

    # Extract months from search_date
    df_temp = df.copy()
    df_temp['SearchMonth'] = df_temp['search_date'].dt.month
    df_temp['SearchMonthName'] = df_temp['search_date'].dt.strftime('%B')

    # Filter for Sep(9), Oct(10), Nov(11), Dec(12), Jan(1)
    valid_months = [1, 9, 10, 11, 12]
    valid_data = df_temp[df_temp['SearchMonth'].isin(valid_months)][['SearchMonth', 'SearchMonthName']].drop_duplicates()

    # Sort months properly
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    valid_data['SortOrder'] = valid_data['SearchMonth'].map(month_order)
    valid_data = valid_data.sort_values('SortOrder')

    month_options = ["All"] + valid_data['SearchMonthName'].unique().tolist()
    return month_options, "All"

# Callback to update search date options (Chart 2)
@app.callback(
    Output("search-date-filter-2", "options"),
    Output("search-date-filter-2", "value"),
    Input("dataset-origin-2", "value")
)
def update_search_dates_2(selected_dataset_origin):
    if selected_dataset_origin not in datasets:
        return [], None

    df = datasets[selected_dataset_origin]

    # Extract months from search_date
    df_temp = df.copy()
    df_temp['SearchMonth'] = df_temp['search_date'].dt.month
    df_temp['SearchMonthName'] = df_temp['search_date'].dt.strftime('%B')

    # Filter for Sep(9), Oct(10), Nov(11), Dec(12), Jan(1)
    valid_months = [1, 9, 10, 11, 12]
    valid_data = df_temp[df_temp['SearchMonth'].isin(valid_months)][['SearchMonth', 'SearchMonthName']].drop_duplicates()

    # Sort months properly
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    valid_data['SortOrder'] = valid_data['SearchMonth'].map(month_order)
    valid_data = valid_data.sort_values('SortOrder')

    month_options = ["All"] + valid_data['SearchMonthName'].unique().tolist()
    return month_options, "All"

def style_cyberpunk_figure(fig, line_color=None, title=""):
    """Applies the dark modern aesthetic to Plotly figures."""
    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot background
        paper_bgcolor=PANEL_BG,        # Match panel background
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=50, r=30, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, tickprefix="$"),
    )
    if line_color:
        fig.update_traces(
            line=dict(color=line_color, width=3),
            marker=dict(size=8, color=line_color, line=dict(width=2, color=BG_COLOR)),
            mode="lines+markers"
        )
    return fig

def filter_by_month_name(df, month_name):
    """Filter dataframe by month name (Sep, Oct, Nov, Dec, Jan)"""
    if month_name == "All":
        valid_months = [1, 9, 10, 11, 12]
        return df[df['search_date'].dt.month.isin(valid_months)]
    else:
        return df[df['search_date'].dt.strftime('%B') == month_name]

# =====================================================================
# 6️⃣ AGGREGATION FUNCTION WITH CO2 DATA
# =====================================================================
def aggregate_price_data(filtered_df, agg_method='mean'):
    """
    Aggregate price data by date, preserving airline and CO2 information.
    For each date, calculate the mean/median price and average the CO2 values.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    agg_dict = {
        'Price': agg_method,
        'Airline': lambda x: ', '.join(x.dropna().unique()),  # Concatenate unique airlines
        'AvgCO2': 'mean'  # Average CO2 per hour
    }

    agg_df = filtered_df.groupby('Date').agg(agg_dict).reset_index()
    agg_df.columns = ['Date', 'Price', 'Airline', 'AvgCO2']

    return agg_df.sort_values('Date')

@app.callback(
    Output("merged-price-chart", "figure"),
    Input("dataset-origin-1", "value"),
    Input("destination-filter-1", "value"),
    Input("airline-filter-1", "value"),
    Input("search-date-filter-1", "value"),
    Input("dataset-origin-2", "value"),
    Input("destination-filter-2", "value"),
    Input("airline-filter-2", "value"),
    Input("search-date-filter-2", "value"),
    Input("agg-method", "value")
)
def update_merged_chart(orig1, dest1, air1, month1, orig2, dest2, air2, month2, agg_method):
    """
    Display both TRACKER ALPHA and TRACKER BETA on the same chart for direct comparison
    """
    fig = go.Figure()

    hover_template = (
            "<b>Date:</b> %{x|%b %d, %Y}<br>" +
            "<b>Airline:</b> %{customdata[0]}<br>" +
            "<b>Price:</b> $%{y:.2f}<br>" +
            "<b>AVG CO2:</b> %{customdata[1]:.2f} kg/hr<br>" +
            "<extra></extra>"
    )

    def process(orig, dest, air, month_name):
        if orig not in datasets:
            return pd.DataFrame()

        df = datasets[orig].copy()

        # Filter by destination
        if dest != "All":
            df = df[df["Destination"] == dest]

        # Filter by airline
        if air != "All":
            df = df[df["Airline"] == air]

        # Filter by month
        df = filter_by_month_name(df, month_name)

        if df.empty:
            return df

        # Aggregate by date ONLY (one point per date across all airlines)
        agg_dict = {
            'Price': agg_method,
            'Airline': lambda x: ', '.join(x.dropna().unique()),  # Concatenate unique airlines
            'AvgCO2': 'mean'  # Average CO2 per hour
        }
        agg_data = df.groupby('Date').agg(agg_dict).reset_index()

        return agg_data

    # Get data for both trackers
    agg1 = process(orig1, dest1, air1, month1)
    agg2 = process(orig2, dest2, air2, month2)

    # Add TRACKER ALPHA
    if not agg1.empty:
        label = f"ALPHA ({orig1} → {dest1})" if dest1 != "All" else f"ALPHA ({orig1})"
        fig.add_trace(go.Scatter(
            x=agg1["Date"],
            y=agg1["Price"],
            customdata=agg1[["Airline", "AvgCO2"]],
            hovertemplate=hover_template,
            mode="lines+markers",
            name=label,
            line=dict(color=NEON_CYAN, width=3),
            marker=dict(size=8, color=NEON_CYAN, line=dict(width=2, color=BG_COLOR))
        ))

    # Add TRACKER BETA
    if not agg2.empty:
        label = f"BETA ({orig2} → {dest2})" if dest2 != "All" else f"BETA ({orig2})"
        fig.add_trace(go.Scatter(
            x=agg2["Date"],
            y=agg2["Price"],
            customdata=agg2[["Airline", "AvgCO2"]],
            hovertemplate=hover_template,
            mode="lines+markers",
            name=label,
            line=dict(color=NEON_PINK, width=3),
            marker=dict(size=8, color=NEON_PINK, line=dict(width=2, color=BG_COLOR))
        ))

    metric = "MEDIAN" if agg_method == "median" else "MEAN"
    if agg1.empty and agg2.empty:
        title = f"NO SIGNAL: Adjust parameters to load {metric} Price Comparison"
    else:
        title = f"PRICE COMPARISON MATRIX: {metric} Price Trends (ALPHA vs BETA)"

    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, title="Departure Date"),
        yaxis=dict(showgrid=True, gridcolor="#333", zeroline=False, tickprefix="$", title=f"{metric} Price ($)"),
        hovermode="x unified"
    )

    return fig

# =====================================================================
# 6️⃣ MONTHLY AGGREGATION FUNCTION
# =====================================================================
def aggregate_price_by_month(filtered_df, agg_method='mean'):
    """
    Aggregate price data by month (Sep, Oct, Nov, Dec, Jan).
    For each month, calculate the mean/median price.
    """
    if filtered_df.empty:
        return pd.DataFrame()

    # Extract month from Date column
    filtered_df = filtered_df.copy()
    filtered_df['Month'] = filtered_df['Date'].dt.month
    filtered_df['MonthName'] = filtered_df['Date'].dt.strftime('%B')

    # Filter for months Sep(9), Oct(10), Nov(11), Dec(12), Jan(1)
    valid_months = [1, 9, 10, 11, 12]
    filtered_df = filtered_df[filtered_df['Month'].isin(valid_months)]

    if filtered_df.empty:
        return pd.DataFrame()

    # Aggregate by month
    agg_dict = {
        'Price': agg_method,
    }

    monthly_agg = filtered_df.groupby(['Month', 'MonthName']).agg(agg_dict).reset_index()
    monthly_agg.columns = ['Month', 'MonthName', 'Price']

    # Sort by month (Jan first, then Sep-Dec)
    month_order = {1: 0, 9: 1, 10: 2, 11: 3, 12: 4}
    monthly_agg['SortOrder'] = monthly_agg['Month'].map(month_order)
    monthly_agg = monthly_agg.sort_values('SortOrder').drop('SortOrder', axis=1)

    return monthly_agg

# =====================================================================
# 7️⃣ ROUTE ANALYTICS - Calculate AVG prices for all routes
# =====================================================================

# Helper: Generate color gradients
def interpolate_color(color1, color2, factor):
    """Linear interpolation between two colors (hex format)"""
    c1_rgb = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
    c2_rgb = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
    result = tuple(int(c1_rgb[i] + (c2_rgb[i] - c1_rgb[i]) * factor) for i in range(3))
    return '#{:02x}{:02x}{:02x}'.format(*result)

def get_color_gradient(values, dark_color, light_color):
    """Create gradient colors based on values (0=dark, 1=light)"""
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    colors = []
    for val in values:
        factor = (val - min_val) / range_val
        color = interpolate_color(dark_color, light_color, factor)
        colors.append(color)
    return colors

def calculate_route_analytics(datasets):
    """Calculate average prices for all routes across all datasets"""
    route_prices = {}

    for origin_code, df in datasets.items():
        for destination in df['Destination'].unique():
            route_key = f"{origin_code}-{destination}"
            route_data = df[df['Destination'] == destination]
            avg_price = route_data['Price'].mean()
            route_prices[route_key] = avg_price

    return route_prices


# Callback for cheapest routes chart
@app.callback(
    Output("cheapest-routes-chart", "figure"),
    Input("destination-checklist-cheapest", "value")
)
def update_cheapest_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filter by selected destinations
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Sort and get 10 cheapest, reverse to show cheapest at the top
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1])[:10]
    sorted_routes.reverse()  # Reverse so cheapest is at the top
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    # Dark purple for cheapest (top), light purple for more expensive
    colors = get_color_gradient(prices, '#3d1a4d', '#c9a0dc')
    # White for cheapest (top), dark purple for more expensive
    colors = get_color_gradient(prices, '#ffffff', '#3d1a4d')

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="10 CHEAPEST ROUTES",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Price ($)"),
        yaxis=dict(showgrid=False, title="Route"),
        height=400
    )

    return fig

# Callback for most expensive routes chart
@app.callback(
    Output("expensive-routes-chart", "figure"),
    Input("destination-checklist-expensive", "value")
)
def update_expensive_routes(selected_destinations):
    route_prices = calculate_route_analytics(datasets)

    # Filter by selected destinations
    if selected_destinations:
        filtered_routes = {k: v for k, v in route_prices.items()
                           if k.split('-')[1] in selected_destinations}
    else:
        filtered_routes = route_prices

    # Sort and get 10 most expensive, reverse to show most expensive at the top
    sorted_routes = sorted(filtered_routes.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_routes.reverse()  # Reverse so most expensive is at the top
    routes = [r[0] for r in sorted_routes]
    prices = [r[1] for r in sorted_routes]

    # Dark magenta for most expensive (top), light magenta for cheaper
    colors = get_color_gradient(prices, '#6b0080', '#e6b3ff')

    fig = px.bar(
        x=prices,
        y=routes,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="10 MOST EXPENSIVE ROUTES",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Price ($)"),
        yaxis=dict(showgrid=False, title="Route"),
        height=400
    )

    return fig

# Callback for origin comparison chart with destination filters
@app.callback(
    Output("origin-comparison-chart", "figure"),
    Input("destination-checklist", "value")
)
def update_origin_comparison(selected_destinations):
    origin_avg_prices = {}

    for origin_code, df in datasets.items():
        if selected_destinations:
            # Filter by selected destinations
            filtered_df = df[df['Destination'].isin(selected_destinations)]
        else:
            # If no destinations selected, use all
            filtered_df = df

        if not filtered_df.empty:
            avg_price = filtered_df['Price'].mean()
            origin_avg_prices[origin_code] = avg_price

    origins = list(origin_avg_prices.keys())
    prices = list(origin_avg_prices.values())

    # Dark cyan for most expensive, light cyan for cheaper
    colors = get_color_gradient(prices, '#003d4d', '#99e6f0')

    fig = px.bar(
        x=prices,
        y=origins,
        orientation='h',
        text=prices
    )

    fig.update_traces(
        marker_color=colors,
        texttemplate='$%{text:.2f}',
        textposition='outside',
        textfont=dict(color=TEXT_MUTED, size=11)
    )

    fig.update_layout(
        title="ORIGIN AIRPORT AVG PRICE COMPARISON",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor=PANEL_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI"),
        margin=dict(l=80, r=80, t=60, b=50),
        xaxis=dict(showgrid=True, gridcolor="#333", title="Average Price ($)"),
        yaxis=dict(showgrid=False, title="Origin Airport"),
        height=400
    )

    return fig

# =====================================================================
# 5️⃣ DATASET LOADING — module level (runs on import AND on direct run)
# =====================================================================
print("Loading datasets (edit5)...")
datasets = {}
for origin_code, file_path in DATASET_PATHS.items():
    try:
        df = load_data_from_file(file_path)
        datasets[origin_code] = df
        print(f"✓ Loaded {origin_code}: {len(df)} records")
    except Exception as e:
        print(f"✗ Error loading {origin_code} from {file_path}: {e}")

if not datasets:
    print("WARNING: No datasets loaded — app will show empty state.")

print(f"\n✓ Successfully loaded {len(datasets)} datasets\n")

# =====================================================================
# 6️⃣ ENTRY POINT (local dev only)
# =====================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8057))
    app.run(host="0.0.0.0", port=port, debug=False)
