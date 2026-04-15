# ✈ NEURAL FLIGHT ANALYTICS PLATFORM
### Ekonomicko-statistická analýza cen letů a emisí CO₂ — střední Evropa

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-66fcf1?style=for-the-badge&logo=python&logoColor=white&labelColor=1f2833)
![Dash](https://img.shields.io/badge/Plotly_Dash-2.17-ff007f?style=for-the-badge&logo=plotly&logoColor=white&labelColor=1f2833)
![Docker](https://img.shields.io/badge/Docker-Containerized-45a29e?style=for-the-badge&logo=docker&logoColor=white&labelColor=1f2833)
![DigitalOcean](https://img.shields.io/badge/DigitalOcean-Deployed-0080FF?style=for-the-badge&logo=digitalocean&logoColor=white&labelColor=1f2833)

</div>

---

## 📋 O projektu

**Neural Flight Analytics Platform** je datová analytická aplikace zaměřená na sledování a analýzu cen letů z pěti středoevropských letišť do čtyř klíčových destinací. Projekt kombinuje sběr dat, statistickou analýzu a interaktivní vizualizace do jednoho deployovaného webového prostředí.

Projekt vznikl jako nástroj pro:
- 📊 Sledování vývoje cen letenek v čase (booking curve)
- 🌍 Analýzu uhlíkové stopy jednotlivých letů a leteckých společností
- 💡 Ekonomicko-statistické hodnocení cenové nerovnoměrnosti (Gini koeficient)
- 🗺️ Vizualizaci cenových toků mezi letišti (Sankey diagram)

---

## 🗺️ Sledované trasy

| Origin | Destinace | Letecké společnosti |
|--------|-----------|---------------------|
| 🇨🇿 **PRG** — Praha | AMS · BCN · FCO · LON | Ryanair, Easyjet, Smartwings, KLM, Vueling |
| 🇵🇱 **WAW** — Varšava | AMS · BCN · FCO · LON | LOT, Ryanair, Wizz Air, Easyjet |
| 🇩🇪 **BER** — Berlín | AMS · BCN · FCO · LON | Ryanair, Easyjet, British Airways |
| 🇦🇹 **VIE** — Vídeň | AMS · BCN · FCO · LON | Austrian Airlines, Vueling, KLM |
| 🇭🇺 **BUD** — Budapešť | AMS · BCN · FCO · LON | Wizz Air, Ryanair, Easyjet |

---

## 🚀 Funkce aplikace

### 📈 Booking Curve Analyzer — `vizualizationFlightOffers`
> *Jak se mění cena letenky v závislosti na předstihu nákupu?*

- Zobrazuje vývoj cen pro každý konkrétní datum letu sledovaný v průběhu sběru dat
- **Denní režim** — jedna čára = jeden datum odletu, osa X = datum sledování (scraping date)
- **Měsíční režim** — agregace cen dle měsíce odletu, zobrazení **průměru i mediánu** současně s Δ anotací rozdílu
- Filtry: Origin · Destinace · Aerolinka · Typ letadla · Agregační metoda

---

### ✈️ January Flight Tracker — `vizualizationJanuary`
> *Multioriginové srovnání cen na stejné destinace v lednu 2026*

- Paralelní srovnání cen ze všech 5 letišť na stejné destinaci
- Identifikace nejlevnějšího a nejdražšího originu pro danou trasu
- Srovnání průměrných cen dle dne v týdnu a hodiny odletu
- Interaktivní filtry s real-time aktualizací grafů

---

### 🌍 Emission Intelligence System — `vizualizationEmision`
> *Uhlíková stopa letů — srovnání aerolinií, letadel a tras*

Tři režimy emisní analýzy:

| Režim | Metrika | Použití |
|-------|---------|---------|
| **AVG CO₂ (kg/hr)** | Průměrná emise motoru za hodinu letu | Srovnání efektivity motorů |
| **Est. CO₂ (kg/flight)** | Odhadovaná celková emise za jeden let | Environmentální dopad konkrétní trasy |
| **Emission/Seat (kg/hr)** | Emise na jedno sedadlo za hodinu | Nejfairnetřejší srovnání mezi letadly různé velikosti |

- Skupinování tras dle **aerolinie**, **typu letadla** nebo **routy**
- Hover tooltip: cena letenky · aerolinka · typ letadla · emise/sedadlo
- Statistická lišta: mean · median · min · max · počet záznamů

---

### 🗺️ Route Sankey Diagram — `vizualizationSankey`
> *Vizualizace cenových toků mezi letišti*

- Sankey diagram zobrazující průměrné nebo mediánové ceny na všech 20 trasách
- **Přepínání statistické metody** — Mean vs. Median s barevným odlišením
- Filtry: Origin · Destinace · Statistická metoda
- Statistická lišta se srovnáním mean/median/Δ pro každou aktivní trasu

---

## 📐 Emise — metodologie výpočtu

Emise jsou počítány na základě specifické spotřeby paliva a emisního faktoru pro každou kombinaci **aerolinka + typ letadla**:

```
Est. Fuel (kg)          = est_fuel_per_hour × duration_hours
Est. CO₂ (kg)           = est_co2_per_hour  × duration_hours
AVG CO₂ (kg/hr)         = est_co2_per_hour
emissions_per_seat (AVG) = AVG CO₂ (kg/hr) ÷ configured_seats
```

Zahrnuto **39 kombinací** aerolinka/letadlo napříč všemi operátory (Austrian Airlines, British Airways, Easyjet, KLM, LOT, Ryanair, Ryanair UK, Smartwings, Vueling, Wizz Air).

---

## 📊 Datová pipeline

```
Zdrojová data (scraping)
        │
        ▼
 match_flights.py          ← párování letů se skutečnými operačními daty
        │
        ▼
 fix_vie_canceled.py       ← čištění VIE datasetu
        │
        ▼
 PRG_1_0.py / WAW_1_0.py   ← statistická analýza, výpočet emisí,
 VIE_1_0.py / BER_1_0.py      generování _form.csv pro vizualizace
 BUD_1_0.py
        │
        ▼
   _form.csv soubory        ← čistá data připravená pro dashboard
        │
        ▼
   Dash aplikace            ← interaktivní vizualizace
```

### Výstupní sloupce `_form.csv`

```
search_date ; flight_date ; origin ; destination ; departure_time ;
duration ; price ; airline_details ; Est. Fuel (kg) ; Est. CO2 (kg) ;
AVG CO2 (kg/hr) ; aircraft ; emissions_per_seat (AVG)
```

---

## 🐳 Spuštění projektu

### Lokálně

```bash
# 1. Klonování repozitáře
git clone https://github.com/mFadrhons/NeuralVizualizationApp.git
cd NeuralVizualizationApp

# 2. Vytvoření virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 3. Instalace závislostí
pip install -r requirements.txt

# 4. Nastavení prostředí
copy .env.example .env          # Windows
# cp .env.example .env          # Mac/Linux
# Uprav LOCAL_DATA_PATH v .env

# 5. Spuštění
python main_page.py
# → http://localhost:8080
```

### Docker

```bash
# Build a spuštění
docker-compose --profile dashboards up --build

# Spuštění datových procesorů (generování _form.csv)
docker-compose --profile processors run --rm proc-prg
```

### Porty

| Služba | Port | URL |
|--------|------|-----|
| Main Dashboard | 8080 | `http://localhost:8080` |
| Booking Curve | 8052 | `http://localhost:8052` |
| January Tracker | 8051 | `http://localhost:8051` |
| Emission System | 8053 | `http://localhost:8053` |
| Sankey Diagram | 8054 | `http://localhost:8054` |

---

## ⚙️ Konfigurace prostředí

Projekt používá `config.py` pro správu cest v různých prostředích:

```python
# Lokální vývoj
APP_ENV=local   → C:/Users/.../SAVE/FORM/

# Cloud (DigitalOcean)
APP_ENV=cloud   → data/FORM/
```

Nastavení přes proměnnou prostředí:
```bash
# .env soubor
APP_ENV=cloud
LOCAL_DATA_PATH=C:/Users/mFadrhons/Documents/WS/repository/SAVE
```

---

## 🏗️ Struktura projektu

```
NeuralVizualizationApp/
│
├── 📊 Vizualizace
│   ├── main_page.py                  ← hlavní dashboard + routing
│   ├── app_instance.py               ← sdílená Dash instance
│   ├── vizualizationFlightOffers.py  ← booking curve analyzer
│   ├── vizualizationJanuary.py       ← january flight tracker
│   ├── vizualizationEmision.py       ← emission intelligence
│   └── vizualizationSankey.py        ← route sankey diagram
│
├── 🔧 Datová pipeline
│   ├── PRG_1_0.py                    ← zpracování PRG dat
│   ├── WAW_1_0.py                    ← zpracování WAW dat
│   ├── VIE_1_0.py                    ← zpracování VIE dat
│   ├── BER_1_0.py                    ← zpracování BER dat
│   ├── BUD_1_0.py                    ← zpracování BUD dat
│   ├── match_flights.py              ← párování letů
│   └── fix_vie_canceled.py           ← čištění VIE datasetu
│
├── 📈 Analýza
│   └── gini_calculator.py            ← True Gini koeficient
│
├── ⚙️ Konfigurace
│   ├── config.py                     ← správa cest (local/cloud)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── .gitignore
│   └── .dockerignore
│
└── 📁 data/
    └── FORM/                         ← _form.csv soubory (5× ~2MB)
        ├── PRG_form.csv
        ├── WAW_form.csv
        ├── VIE_form.csv
        ├── BER_form.csv
        └── BUD_form.csv
```

---

## 📦 Technologie

| Kategorie | Technologie |
|-----------|-------------|
| Backend | Python 3.11 |
| Web framework | Plotly Dash 2.17 + Flask |
| Vizualizace | Plotly Graph Objects |
| Data processing | Pandas 2.2, NumPy 1.26 |
| Statistika | SciPy 1.13, Seaborn |
| Produkční server | Gunicorn 22 |
| Kontejnerizace | Docker + Docker Compose |
| Cloud deployment | DigitalOcean App Platform |

---

## 📚 Reference

- **Santos, C. M. L. & Dias, C. P. S.** (2024). *An assessment of the true Gini coefficient regarding the fulfilment of the basic criteria for inequality measures.* Acta Scientiarum Technology, v. 46, e64563. DOI: 10.4025/actascitechnol.v46i1.64563
- **Bowles, S. & Carlin, W.** (2020). *Inequality as experienced difference: a reformulation of the Gini coefficient.* Economics Letters, 186, 108789.

---

## 👤 Autor

**Martin Fadrhonc**
Prague, Czech Republic
GitHub: [@mFadrhons](https://github.com/mFadrhons)

---

<div align="center">
<sub>Built with ◈ NEURAL FLIGHT ANALYTICS PLATFORM ◈</sub>
</div>
