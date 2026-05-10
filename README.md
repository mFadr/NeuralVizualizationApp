# Neural Flight Analytics Platform

Ekonomicko-statistická analýza cen letů a emisí CO2 ze středoevropských letišť.

## O projektu

Neural Flight Analytics Platform je datová analytická aplikace zaměřená na sledování a analýzu cen letů z pěti středoevropských letišť do čtyř klíčových destinací. Projekt kombinuje sběr dat, statistickou analýzu a interaktivní vizualizace do jednoho deployovaného webového prostředí.

Projekt vznikl jako nástroj pro:

- sledování vývoje cen letenek v čase (booking curve)
- analýzu uhlíkové stopy jednotlivých letů a leteckých společností
- ekonomicko-statistické hodnocení cenové nerovnoměrnosti pomocí Gini koeficientu
- vizualizaci cenových toků mezi letišti (Sankey diagram)

## Sledované trasy

Aplikace pokrývá pět zdrojových letišť ve střední Evropě a čtyři klíčové destinace (AMS, BCN, FCO, LON), tedy celkem 20 tras.


VÝCHOZÍ LETIŠTĚ
| Kód | Letiště | Letecké společnosti |
|-----|---------|---------------------|
| PRG | Praha | Ryanair, Easyjet, Smartwings, KLM, Vueling |
| WAW | Varšava | LOT, Ryanair, Wizz Air, Easyjet |
| BER | Berlín | Ryanair, Easyjet, British Airways |
| VIE | Vídeň | Austrian Airlines, Vueling, KLM |
| BUD | Budapešť | Wizz Air, Ryanair, Easyjet |


DESTINACE
| Kód | Letiště | Letecké společnosti |
|-----|---------|---------------------|
| AMS | Amsterdam | KLM, Easyjet, LOT, Austrian Airlines |
| BCN | Barcelona  | LOT, Ryanair, Wizz Air, Easyjet, Austrian Airlines, Vueling,  Smartwings |
| FCO | Řim | Ryanair, Easyjet,  Wizz Air, Smartwings, Austrian Airlines, LOT |
| LON | Londýn | British Airways, Ryanair, Ryanair UK ,Wizz Air, Easyjet, Austrian Airlines, LOT |



Letecké společnosti jsou v aplikaci klasifikovány do dvou skupin pro snadnější filtraci:

- **Tradiční**: Austrian Airlines, KLM, British Airways, LOT Polish Airlines
- **Nízkonákladové**: easyJet, Wizz Air, Wizz Air Malta, Vueling Airlines, Wizz Air UK, Smartwings, Ryanair

## Funkce aplikace

Aplikace obsahuje šest analytických modulů, dostupných z hlavního dashboardu (`mainPage.py`).

### Booking Curve Analyzer — `vizualizationFlightOffers.py`

Sleduje vývoj cen letenek v čase, tedy jak se mění cena v závislosti na předstihu nákupu.

- denní režim: jedna čára = jeden datum odletu, osa X = datum sledování
- měsíční režim: agregace cen dle měsíce odletu, zobrazení průměru i mediánu současně
- filtry: výchozí letiště, destinace, datum odletu spoje, letecká společnost
- filtr leteckých společností je dvousloupcový (Tradiční vs. Nízkonákladové) s master přepínačem „Všechny letecké společnosti"
- filtr stavu letů: zahrnout zrušené lety nebo pouze uskutečněné

### January Flight Tracker — `vizualizationJanuary.py`

Multioriginové srovnání cen na stejné destinaci. Obsahuje dva nezávislé „Tracker" panely (Alfa a Beta), které lze nastavit na různé výchozí letiště nebo destinace a přímo srovnat na jednom grafu.

- pořadí filtrů: počáteční letiště, destinace, výběr měsíců pro zobrazení, letecká společnost
- filtr měsíců s lokalizovanou nabídkou v češtině: Září 2025, Říjen 2025, Listopad 2025, Prosinec 2025, Leden 2026 (s master přepínačem „Vše")
- filtr leteckých společností je dvousloupcový s master přepínačem
- agregační metoda (průměr nebo medián) platí pro oba trackery najednou

### Emission Intelligence System — `vizualizationEmision.py`

Analyzuje uhlíkovou stopu letů a srovnává emise CO2 dle aerolinky, typu letadla nebo trasy.

| Režim | Metrika | Použití |
|-------|---------|---------|
| AVG CO2 (kg/hr) | průměrná emise motoru za hodinu letu | srovnání efektivity motorů |
| Est. CO2 (kg/let) | odhadovaná celková emise za jeden let | environmentální dopad konkrétní trasy |
| Emise/Sedadlo (kg/hr) | emise na jedno sedadlo za hodinu | nejférovější srovnání mezi letadly různé velikosti |

- pořadí filtrů: výchozí letiště, destinace, letecká společnost
- filtr leteckých společností je dvousloupcový (sloupce vedle sebe)
- skupinování tras dle letecké společnosti, typu letadla nebo trasy

### Route Sankey Diagram — `vizualizationSankey.py`

Vizualizuje průměrné nebo mediánové ceny jako tok mezi zdrojovými a cílovými letišti.

- vícenásobný výběr výchozích letišť i destinací (zaškrtávací pole)
- přepínání statistické metody mezi průměrem a mediánem s barevným odlišením
- statistická lišta se srovnáním průměru, mediánu a Δ rozdílu pro každou aktivní trasu
- filtr datového rozsahu: všechna data nebo pouze odlétnuté lety

### Gini Analyzer — `vizualizationGini.py`

Měří cenovou nerovnoměrnost pomocí True Gini koeficientu (Santos & Dias, 2024). Čím vyšší hodnota, tím větší rozptyl cen na dané trase.

- dva režimy zobrazení: horizontální sloupcový graf seřazený dle Gini, nebo heatmapa (matice výchozí letiště × destinace)
- referenční tabulka s interpretací hodnot

### Routes Overview — `vizualizationRoutes.py`

Přehled všech 20 sledovaných tras s rozdělením do tří grafů: 10 nejlevnějších linek, 10 nejdražších linek a porovnání cenových úrovní výchozích letišť.

- filtry destinací pro každý graf nezávisle
- panel SYSTÉMOVÉ PARAMETRY: filtr zrušených letů a agregační metoda (průměr/medián), platí pro všechny tři grafy

### Manual — `vizualizationManual.py`

Uživatelský manuál aplikace s detailním popisem všech filtrů, kroků a interpretací u jednotlivých vizualizačních modulů. Manuál je dostupný i z pravého panelu hlavního dashboardu.

## Hlavní dashboard

Hlavní stránka (`mainPage.py`) představuje rozcestník aplikace s následujícími prvky:

- nadpis a podtitulek nahoře
- KPI karty s celkovými metrikami (počet letišť, záznamů, tras, průměrná a rozpětí cen)
- stavová lišta s informací o načtených datasetech
- mřížka šesti modulových karet (3 + 3) — každá modul je samostatný odkaz
- levý postranní panel: Traffic Analytics (sledování návštěvnosti dashboardu)
- pravý postranní panel: Manual for apps functions (odkaz na manuál)

Layout je 3sloupcový a symetrický. KPI karty mají výrazně tmavší pozadí, aby byly vizuálně oddělené od interaktivních modulových karet.

## Emise — metodologie výpočtu

Emise jsou počítány na základě specifické spotřeby paliva a emisního faktoru pro každou kombinaci aerolinka + typ letadla:

```
Est. Fuel (kg)            = est_fuel_per_hour × duration_hours
Est. CO2 (kg)             = est_co2_per_hour  × duration_hours
AVG CO2 (kg/hr)           = est_co2_per_hour
emissions_per_seat (AVG)  = AVG CO2 (kg/hr) ÷ configured_seats
```

Zahrnuto 39 kombinací aerolinka/letadlo napříč všemi operátory (Austrian Airlines, British Airways, Easyjet, KLM, LOT, Ryanair, Ryanair UK, Smartwings, Vueling, Wizz Air).

## Datová pipeline

Datová pipeline aplikace probíhá ve třech hlavních fázích: sběr dat, postupné zpracování (čištění a obohacení) a generování finálních datasetů pro vizualizaci.

### Zdrojová data ze scrapingu

Aplikace pracuje se dvěma nezávislými zdroji dat, které jsou později propojeny.

**Cenová data** (web prodejců letenek) zachycují cenu, čas odletu, dobu trvání letu a leteckou společnost pro každou kombinaci výchozí letiště + destinace + datum letu, sledovanou v určitý den (`scraping_date`).

```
scraping_date,departure_date,origin,destination,departure_time,flight_duration,price,airline
2025-09-01,2026-01-01,PRG,AMS,09:20 AM,1h 45min,US$59.47,Easyjet
2025-09-01,2026-01-02,PRG,AMS,08:30 PM,1h 45min,US$71.83,Easyjet
2025-09-01,2026-01-03,PRG,AMS,07:25 PM,1h 40min,US$93.62,Easyjet
2025-09-01,2026-01-04,PRG,AMS,08:40 PM,1h 40min,US$76.82,Easyjet
2025-09-01,2026-01-05,PRG,AMS,06:25 PM,1h 40min,US$79.57,Easyjet
2025-09-01,2026-01-06,PRG,AMS,11:35 AM,1h 35min,US$97.31,KLM
```

**Provozní data** (FlightRadar24) doplňují skutečné operační informace o letech, zejména typ letadla, registraci, plánované a skutečné časy odletu a status letu.

```
Date,Origin,Destination,Flight Number,Aircraft,Duration,Sched Dep,Actual Dep,Sched Arr,Status
2026-01-01,PRG,AMS,U27926,A20N (OE-LSV),1:24,09:20 AM,10:08 AM,11:05 AM,Landed 11:32
2026-01-02,PRG,AMS,U27926,A20N (OE-LSW),1:08,08:30 PM,09:28 PM,10:10 PM,Landed 22:36
2026-01-03,PRG,AMS,U27928,-,-,09:54 PM,-,-,FLIGHT CANCELED/NOT OPERATED
2026-01-04,PRG,AMS,U27928,-,-,09:54 PM,-,-,FLIGHT CANCELED/NOT OPERATED
2026-01-05,PRG,AMS,U27928,A319 (OE-LKY),1:05,06:25 PM,09:54 PM,08:05 PM,Landed 22:59
2026-01-06,PRG,AMS,KL1354,B738 (PH-BXA),1:08,11:35 AM,04:25 PM,01:15 PM,Landed 17:33
```

Klíčové rozdíly mezi zdroji:

- cenová data obsahují cenu, ale neznají typ letadla
- provozní data znají typ letadla a status letu, ale neobsahují cenu
- propojením podle (origin, destination, departure_date / Date) se získá kompletní záznam o letu

### Postupné zpracování zdrojových dat

Skripty pro čištění a obohacení dat jsou umístěny ve složce `DataPreparing/` a musí být spouštěny ve specifickém pořadí, protože každý další skript navazuje na výstup předchozího.

| Pořadí | Skript | Účel |
|--------|--------|------|
| 1 | `filter_csv.py` | odstranění chybně nasbíraných dat z jiných leteckých linek |
| 2 | `matchFlights.py` | párování letů se skutečnými operačními daty z FlightRadar24 |
| 3 | `timeAdjustment.py` | sjednocení formátu času napříč zdroji |
| 4 | `fixCanceledFlight.py` | označení letů, ke kterým byla nasbírána cenová data, ale poté byly zrušeny |
| 5 | `fixAirlines.py` | sjednocení názvů aerolinek (např. EasyJet vs. easyJet, LOT vs. LOT Polish Airlines) |
| 6 | `splitAircraftColumn.py` | rozdělení sloupce Aircraft (např. `A20N (OE-LSV)`) na dva samostatné sloupce: typ letadla a registrace |

Po těchto šesti krocích jsou data připravena pro statistickou analýzu a výpočet emisí.

### Generování finálních datasetů

Pro každé výchozí letiště existuje samostatný skript, který provede statistickou analýzu, dopočítá emise CO2 (na základě kombinace aerolinka + typ letadla) a vygeneruje finální `_form.csv` soubor pro dashboard.

```
Vyčištěná data (po DataPreparing)
        |
        v
 PRG_1_0.py / WAW_1_0.py    statistická analýza, výpočet emisí,
 VIE_1_0.py / BER_1_0.py    generování _form.csv pro vizualizace
 BUD_1_0.py
        |
        v
   _form.csv soubory        čistá data připravená pro dashboard
        |
        v
   Dash aplikace            interaktivní vizualizace
```

### Výstupní sloupce `_form.csv`

```
search_date ; flight_date ; origin ; destination ; departure_time ;
duration ; price ; airline_details ; flown_status ; Est. Fuel (kg) ;
Est. CO2 (kg) ; AVG CO2 (kg/hr) ; aircraft ; emissions_per_seat (AVG)
```

## Spuštění projektu

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
python mainPage.py
# http://localhost:8080
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

## Konfigurace prostředí

Projekt používá `config.py` pro správu cest v různých prostředích:

```python
# Lokální vývoj
APP_ENV=local   ->  C:/Users/.../SAVE/FORM/

# Cloud (DigitalOcean)
APP_ENV=cloud   ->  data/FORM/
```

Nastavení přes proměnnou prostředí:

```bash
# .env soubor
APP_ENV=cloud
LOCAL_DATA_PATH=C:/Users/mFadrhons/Documents/WS/repository/SAVE
```

## Struktura projektu

```
NeuralVizualizationApp/
|
|-- Vizualizace
|   |-- mainPage.py                    hlavní dashboard + routing
|   |-- app_instance.py                sdílená Dash instance
|   |-- vizualizationFlightOffers.py   booking curve analyzer
|   |-- vizualizationJanuary.py        january flight tracker
|   |-- vizualizationEmision.py        emission intelligence
|   |-- vizualizationSankey.py         route sankey diagram
|   |-- vizualizationGini.py           gini analyzer
|   |-- vizualizationRoutes.py         routes overview
|   `-- vizualizationManual.py         uživatelský manuál
|
|-- Datová pipeline
|   |-- DataPreparing/                 skripty pro čištění a obohacení dat
|   |   |-- filter_csv.py              odstranění chybně nasbíraných dat
|   |   |-- matchFlights.py            párování letů s daty z FlightRadar24
|   |   |-- timeAdjustment.py          sjednocení formátu času
|   |   |-- fixCanceledFlight.py       označení zrušených letů
|   |   |-- fixAirlines.py             sjednocení názvů aerolinek
|   |   `-- splitAircraftColumn.py     rozdělení Aircraft na typ a registraci
|   |-- PRG_Formatter.py                     statistická analýza + emise pro PRG
|   |-- WAW_Formatter.py                     statistická analýza + emise pro WAW
|   |-- VIE_Formatter.py                     statistická analýza + emise pro VIE
|   |-- BER_Formatter.py                     statistická analýza + emise pro BER
|   `-- BUD_Formatter.py                     statistická analýza + emise pro BUD
|
|-- Konfigurace
|   |-- config.py                      správa cest (local/cloud)
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- docker-compose.yml
|   |-- .env.example
|   |-- .gitignore
|   `-- .dockerignore
|
`-- data/
    `-- FORM/                          _form.csv soubory (5x ~2MB)
        |-- PRG_form.csv
        |-- WAW_form.csv
        |-- VIE_form.csv
        |-- BER_form.csv
        `-- BUD_form.csv
```

## Technologie

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

## Reference

- Santos, C. M. L. & Dias, C. P. S. (2024). *An assessment of the true Gini coefficient regarding the fulfilment of the basic criteria for inequality measures.* Acta Scientiarum Technology, v. 46, e64563. DOI: 10.4025/actascitechnol.v46i1.64563
- Bowles, S. & Carlin, W. (2020). *Inequality as experienced difference: a reformulation of the Gini coefficient.* Economics Letters, 186, 108789.

## Autor

Matěj Fadrhons
Prague, Czech Republic
GitHub: [@mFadr](https://github.com/mFadr)
