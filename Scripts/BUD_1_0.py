import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

from config import COM_PATHS
file_path = COM_PATHS['BUD']

try:
    csv_data = pd.read_csv(file_path)
    print("CSV file loaded successfully into 'csv_data'!")
    print(csv_data.head())
except FileNotFoundError:
    print(f"Error: The file was not found at '{file_path}'.")
except Exception as e:
    print(f"An error occurred while loading the CSV: {e}")

column_names = [
    'collection_date', 'flight_date', 'origin', 'dest', 'sched_dep_time',  # 0-4  PRG_com_US
    'sched_duration', 'price', 'airline', 'flight_status',                  # 5-8  PRG_com_US
    'aircraft', 'actual_duration', 'sched_dep_time_2',                      # 9-11 merged.csv
    'actual_dep_time', 'sched_arr_time', 'actual_arr_time', 'arr_status'    # 12-15 merged.csv
]

df = csv_data.copy()

print(f"DataFrame has {len(df.columns)} columns")
print(f"column_names has {len(column_names)} elements")
print(f"Current columns: {list(df.columns)}")

df.columns = column_names

print("DataFrame 'df' created with updated column names:")
print(df.head())

# =====================================================================
# Emission lookup table
# =====================================================================
# Seat counts from airlineTable.txt (configured capacity per airline)
emision_data = [
    # Austrian Airlines
    {'airline': 'Austrian Airlines', 'aircraft': 'A20N', 'engine': 'PW1100G-JM', 'fuel': 2050, 'co2': 6478, 'seats': 180},
    {'airline': 'Austrian Airlines', 'aircraft': 'A320', 'engine': 'CFM56-5B',   'fuel': 2520, 'co2': 7963, 'seats': 174},
    {'airline': 'Austrian Airlines', 'aircraft': 'A321', 'engine': 'CFM56-5B',   'fuel': 2900, 'co2': 9164, 'seats': 206},
    {'airline': 'Austrian Airlines', 'aircraft': 'E195', 'engine': 'CF34-10E',   'fuel': 2250, 'co2': 7110, 'seats': 120},
    # British Airways
    {'airline': 'British Airways',   'aircraft': 'A319', 'engine': 'V2500-A5',   'fuel': 2231, 'co2': 7050, 'seats': 143},
    {'airline': 'British Airways',   'aircraft': 'A320', 'engine': 'V2500-A5',   'fuel': 2444, 'co2': 7723, 'seats': 180},
    # Easyjet
    {'airline': 'Easyjet',           'aircraft': 'A20N', 'engine': 'LEAP-1A',    'fuel': 2080, 'co2': 6573, 'seats': 186},
    {'airline': 'Easyjet',           'aircraft': 'A21N', 'engine': 'LEAP-1A',    'fuel': 2400, 'co2': 7584, 'seats': 235},
    {'airline': 'Easyjet',           'aircraft': 'A319', 'engine': 'CFM56-5B',   'fuel': 2300, 'co2': 7268, 'seats': 156},
    {'airline': 'Easyjet',           'aircraft': 'A320', 'engine': 'CFM56-5B',   'fuel': 2520, 'co2': 7963, 'seats': 180},
    # KLM
    {'airline': 'KLM',               'aircraft': 'A21N', 'engine': 'LEAP-1A',    'fuel': 2400, 'co2': 7584, 'seats': 227},
    {'airline': 'KLM',               'aircraft': 'B737', 'engine': 'CFM56-7B',   'fuel': 2420, 'co2': 7647, 'seats': 142},
    {'airline': 'KLM',               'aircraft': 'B738', 'engine': 'CFM56-7B',   'fuel': 2530, 'co2': 7995, 'seats': 186},
    {'airline': 'KLM',               'aircraft': 'B739', 'engine': 'CFM56-7B',   'fuel': 2650, 'co2': 8374, 'seats': 188},
    {'airline': 'KLM',               'aircraft': 'E190', 'engine': 'CF34-10E',   'fuel': 2080, 'co2': 6573, 'seats': 100},
    {'airline': 'KLM',               'aircraft': 'E295', 'engine': 'PW1900G',    'fuel': 2240, 'co2': 7078, 'seats': 136},
    {'airline': 'KLM',               'aircraft': 'E75L', 'engine': 'CF34-8E',    'fuel': 1940, 'co2': 6130, 'seats':  88},
    # LOT
    {'airline': 'LOT',               'aircraft': 'B38M', 'engine': 'LEAP-1B',    'fuel': 2015, 'co2': 6367, 'seats': 189},
    {'airline': 'LOT',               'aircraft': 'B738', 'engine': 'CFM56-7B',   'fuel': 2530, 'co2': 7995, 'seats': 186},
    {'airline': 'LOT',               'aircraft': 'E170', 'engine': 'CF34-8E',    'fuel': 1760, 'co2': 5562, 'seats': 176},
    {'airline': 'LOT',               'aircraft': 'E190', 'engine': 'CF34-10E',   'fuel': 2080, 'co2': 6573, 'seats': 106},
    {'airline': 'LOT',               'aircraft': 'E195', 'engine': 'CF34-10E',   'fuel': 2250, 'co2': 7110, 'seats': 118},
    {'airline': 'LOT',               'aircraft': 'E295', 'engine': 'PW1900G',    'fuel': 2240, 'co2': 7078, 'seats': 136},
    {'airline': 'LOT',               'aircraft': 'E75S', 'engine': 'CF34-8E',    'fuel': 1910, 'co2': 6036, 'seats':  82},
    # Ryanair
    {'airline': 'Ryanair',           'aircraft': 'A320', 'engine': 'CFM56-5B',   'fuel': 2520, 'co2': 7963, 'seats': 180},
    {'airline': 'Ryanair',           'aircraft': 'B38M', 'engine': 'LEAP-1B',    'fuel': 2015, 'co2': 6367, 'seats': 197},
    {'airline': 'Ryanair',           'aircraft': 'B738', 'engine': 'CFM56-7B',   'fuel': 2530, 'co2': 7995, 'seats': 189},
    # Ryanair UK
    {'airline': 'Ryanair UK',        'aircraft': 'B38M', 'engine': 'LEAP-1B',    'fuel': 2015, 'co2': 6367, 'seats': 197},
    # Smartwings
    {'airline': 'Smartwings',        'aircraft': 'B38M', 'engine': 'LEAP-1B',    'fuel': 2015, 'co2': 6367, 'seats': 189},
    {'airline': 'Smartwings',        'aircraft': 'B738', 'engine': 'CFM56-7B',   'fuel': 2530, 'co2': 7995, 'seats': 189},
    {'airline': 'Smartwings',        'aircraft': 'B739', 'engine': 'CFM56-7B',   'fuel': 2650, 'co2': 8374, 'seats': 212},
    {'airline': 'Smartwings',        'aircraft': 'BCS3', 'engine': 'PW1500G',    'fuel': 1850, 'co2': 5846, 'seats': 149},
    # Vueling
    {'airline': 'Vueling',           'aircraft': 'A20N', 'engine': 'PW1100G-JM', 'fuel': 2050, 'co2': 6478, 'seats': 186},
    {'airline': 'Vueling',           'aircraft': 'A21N', 'engine': 'PW1100G-JM', 'fuel': 2380, 'co2': 7521, 'seats': 236},
    {'airline': 'Vueling',           'aircraft': 'A319', 'engine': 'CFM56-5B',   'fuel': 2300, 'co2': 7268, 'seats': 144},
    {'airline': 'Vueling',           'aircraft': 'A320', 'engine': 'CFM56-5B',   'fuel': 2520, 'co2': 7963, 'seats': 180},
    {'airline': 'Vueling',           'aircraft': 'A321', 'engine': 'V2500-A5',   'fuel': 2813, 'co2': 8889, 'seats': 220},
    # Wizz Air
    {'airline': 'Wizz Air',          'aircraft': 'A21N', 'engine': 'PW1100G-JM', 'fuel': 2380, 'co2': 7521, 'seats': 239},
    {'airline': 'Wizz Air',          'aircraft': 'A321', 'engine': 'V2500-A5',   'fuel': 2813, 'co2': 8889, 'seats': 230},
]

emision_df = pd.DataFrame(emision_data)

lookup = {}
for _, row in emision_df.iterrows():
    key = (row['airline'].lower(), row['aircraft'])
    lookup[key] = {'fuel': row['fuel'], 'co2': row['co2'], 'seats': row['seats']}

def get_emision(airline, aircraft):
    if pd.isna(airline) or pd.isna(aircraft) or str(airline).strip() == '' or str(aircraft).strip() == '':
        return {'fuel': np.nan, 'co2': np.nan, 'seats': np.nan}
    key = (str(airline).lower(), str(aircraft).strip())
    return lookup.get(key, {'fuel': np.nan, 'co2': np.nan, 'seats': np.nan})

df['est_fuel_per_hour'] = df.apply(lambda row: get_emision(row['airline'], row['aircraft'])['fuel'],  axis=1)
df['est_co2_per_hour']  = df.apply(lambda row: get_emision(row['airline'], row['aircraft'])['co2'],   axis=1)
df['seats']             = df.apply(lambda row: get_emision(row['airline'], row['aircraft'])['seats'], axis=1)

# =====================================================================
# Data Cleaning
# =====================================================================
print("Čistím data...")

# A) Price → float
df['price'] = pd.to_numeric(
    df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce'
)

# B) Dates → datetime
invalid_dates = df[~df['collection_date'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
if not invalid_dates.empty:
    print("Invalid dates found:")
    print(invalid_dates['collection_date'])

df['collection_date'] = pd.to_datetime(df['collection_date'], errors='coerce')
if df['collection_date'].isna().any():
    print(f"{df['collection_date'].isna().sum()} dates could not be parsed")

df['flight_date'] = pd.to_datetime(df['flight_date'], errors='coerce')

# C) Clean airline name
df['airline'] = df['airline'].astype(str).str.strip(' .')

# D) Binary canceled indicator
df['is_canceled'] = df['flight_status'].apply(lambda x: 1 if 'CANCELED' in str(x) else 0)

# E) Drop duplicate departure time column
df = df.drop(columns=['sched_dep_time_2'], errors='ignore')

# =====================================================================
# Analytical Attributes
# =====================================================================
print("Vytvářím analytické atributy...")

df['days_to_departure'] = (df['flight_date'] - df['collection_date']).dt.days
df['day_name']          = df['flight_date'].dt.day_name()
df['day_of_week']       = df['flight_date'].dt.dayofweek
df['is_weekend']        = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

df['dep_hour'] = pd.to_datetime(
    df['sched_dep_time'], format='%I:%M %p', errors='coerce'
).dt.hour

def parse_duration(duration_str):
    if pd.isna(duration_str):
        return np.nan
    hours, minutes = 0, 0
    s = str(duration_str)
    if 'h' in s:
        parts = s.split('h')
        hours = int(parts[0].strip())
        if len(parts) > 1 and 'min' in parts[1]:
            minutes = int(parts[1].replace('min', '').strip())
    elif 'min' in s:
        minutes = int(s.replace('min', '').strip())
    return hours + minutes / 60.0

df['duration_hours'] = df['sched_duration'].apply(parse_duration)

# =====================================================================
# Emission calculations  ← must come BEFORE F and G
# =====================================================================
df['Est. Fuel (kg)']           = df['est_fuel_per_hour'] * df['duration_hours']
df['Est. CO2 (kg)']            = df['est_co2_per_hour']  * df['duration_hours']
df['AVG CO2 (kg/hr)']          = df['est_co2_per_hour']
# emissions_per_seat (AVG): AVG CO2 kg/hr divided by configured seat count
df['emissions_per_seat (AVG)'] = df.apply(
    lambda row: round(row['AVG CO2 (kg/hr)'] / row['seats'], 4)
    if pd.notna(row['AVG CO2 (kg/hr)']) and pd.notna(row['seats']) and row['seats'] > 0
    else np.nan,
    axis=1
)

# =====================================================================
# F) Flight operation status column
#    Uses est_co2_per_hour — NaN means airline was blank = canceled
# =====================================================================
df['flight_operation_status'] = df['est_co2_per_hour'].apply(
    lambda x: 'Flight Canceled' if pd.isna(x) or x == 0 else 'Operated'
)

# =====================================================================
# G) Fill empty AVG CO2 (kg/hr) with label instead of NaN
#    NOTE: this makes the column mixed type (float + string).
#    All arithmetic on this column must happen ABOVE this line.
# =====================================================================
df['AVG CO2 (kg/hr)'] = df['AVG CO2 (kg/hr)'].apply(
    lambda x: 'Flight Canceled' if pd.isna(x) or x == 0 else x
)

# =====================================================================
# Statistical Tests
# =====================================================================
print("\n--- VÝSLEDKY STATISTICKÝCH TESTŮ ---")

weekend_prices = df[df['is_weekend'] == 1]['price']
weekday_prices = df[df['is_weekend'] == 0]['price']

if len(weekend_prices) > 0 and len(weekday_prices) > 0:
    t_stat, p_val = stats.ttest_ind(weekend_prices, weekday_prices, equal_var=False)
    print(f"Průměrná cena o víkendu: ${weekend_prices.mean():.2f}")
    print(f"Průměrná cena v týdnu:   ${weekday_prices.mean():.2f}")
    print(f"P-hodnota (T-test):       {p_val:.4f}")
    if p_val < 0.05:
        print("-> Závěr: Existuje statisticky významný rozdíl.")
    else:
        print("-> Závěr: Nelze prokázat statisticky významný rozdíl.")

# =====================================================================
# Visualisations
# =====================================================================
print("\nGeneruji vizualizace...")

sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Explorační analýza cen letenek', fontsize=18)

sns.histplot(df['price'], bins=20, kde=True, ax=axes[0, 0], color='skyblue')
axes[0, 0].set_title('Distribuce cen letenek')
axes[0, 0].set_xlabel('Cena (USD)')
axes[0, 0].set_ylabel('Počet letů')

sns.lineplot(data=df, x='days_to_departure', y='price', marker='o', ax=axes[0, 1], color='coral')
axes[0, 1].set_title('Vývoj ceny podle předstihu nákupu')
axes[0, 1].set_xlabel('Počet dní do odletu')
axes[0, 1].set_ylabel('Průměrná cena (USD)')
axes[0, 1].invert_xaxis()

days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
sns.boxplot(data=df, x='day_name', y='price', order=days_order, ax=axes[1, 0],
            hue='day_name', palette='Set2', legend=False)
axes[1, 0].set_title('Volatilita cen v dnech týdne')
axes[1, 0].set_xlabel('Den odletu')
axes[1, 0].set_ylabel('Cena (USD)')
axes[1, 0].tick_params(axis='x', rotation=45)

sns.barplot(data=df, x='dep_hour', y='price', ax=axes[1, 1],
            hue='dep_hour', palette='viridis', errorbar=None, legend=False)
axes[1, 1].set_title('Průměrná cena podle hodiny odletu')
axes[1, 1].set_xlabel('Hodina odletu (0-23)')
axes[1, 1].set_ylabel('Průměrná cena (USD)')

plt.tight_layout()
plt.subplots_adjust(top=0.92)
plt.show()

# =====================================================================
# Export helpers
# =====================================================================
def get_origin_filter_options():
    return df['origin'].dropna().unique().tolist()


def get_csv_string_for_dash():
    export_df = df[[
        'collection_date', 'flight_date', 'origin', 'dest',
        'sched_dep_time', 'sched_duration', 'price', 'airline',
        'Est. Fuel (kg)', 'Est. CO2 (kg)', 'AVG CO2 (kg/hr)',
        'aircraft', 'emissions_per_seat (AVG)'
    ]].copy()

    export_df.rename(columns={
        'collection_date': 'search_date',
        'dest':            'destination',
        'sched_dep_time':  'departure_time',
        'sched_duration':  'duration',
        'airline':         'airline_details'
    }, inplace=True)

    export_df['search_date']  = export_df['search_date'].dt.strftime('%Y-%m-%d')
    export_df['flight_date']  = export_df['flight_date'].dt.strftime('%Y-%m-%d')
    export_df['airline_details'] = export_df['airline_details'].fillna('').astype(str)
    export_df['departure_time']  = export_df['departure_time'].fillna('').astype(str)
    export_df['duration']        = export_df['duration'].fillna('').astype(str)

    return export_df.to_csv(index=False, sep=';')


if __name__ == "__main__":
    print("\n--- ORIGIN FILTER OPTIONS ---")
    print(f"Available origins: {get_origin_filter_options()}")

    csv_output = get_csv_string_for_dash()

    from config import OUTPUT_PATHS
    output_file_path = OUTPUT_PATHS['BUD_form']
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(csv_output)
    print(f"\n✓ Transformed data saved to: {output_file_path}")

    lines = csv_output.split('\n')
    print('\n'.join(lines[:11]))