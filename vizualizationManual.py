from config import SCREENSHOT_FILES

"""
vizualizationManual.py
Komplexní uživatelský manuál pro platformu Neural Flight Analytics.

Manuál obsahuje sedm podstránek:

  1. přehled sledovaných tras  (úvodní rozcestník)
  2. booking curve analyzer    (vizualizationFlightOffers)
  3. january flight tracker    (vizualizationJanuary)
  4. emission intelligence     (vizualizationEmision)
  5. route sankey diagram      (vizualizationSankey)
  6. gini analyzer             (vizualizationGini)
  7. routes overview           (vizualizationRoutes)

Každá podstránka obsahuje náhledový snímek obrazovky a podrobný textový
popis funkcí, ovládacích prvků a způsobu interpretace výstupů.
"""

import os
import base64
from dash import dcc, html, Input, Output, callback_context, ALL

from app_instance import app

# =====================================================================
# 1. cyberpunk téma
# =====================================================================
BG_COLOR    = "#0b0c10"
PANEL_BG    = "#1f2833"
KPI_BG      = "#0d1117"
NEON_CYAN   = "#66fcf1"
NEON_BLUE   = "#45a29e"
NEON_PINK   = "#ff007f"
NEON_PURPLE = "#9d4edd"
NEON_YELLOW = "#f5c518"
NEON_GREEN  = "#39ff14"
NEON_ORANGE = "#ff6600"
TEXT_MUTED  = "#c5c6c7"

# =====================================================================
# 2. seznamy letišť
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

# =====================================================================
# 3. načítání obrázků
# =====================================================================
def _encode_image(filename):
    """převede obrázek do base64 řetězce použitelného v atributu src."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        filename,
        os.path.join(here, filename),
        os.path.join("assets", filename),
        os.path.join(here, "assets", filename),
        os.path.join(here, "..", filename),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
            except Exception:
                continue
    return None




# =====================================================================
# 4. obsah jednotlivých podstránek manuálu
# =====================================================================
PAGES_CONTENT = [
    # =================================================================
    # 1. booking curve analyzer
    # =================================================================
    {
        "id":       "offers",
        "title":    "Historie vývoje cen letenek",
        "subtitle": "křivka vývoje cen rezervací (září 2025 až leden 2026)",
        "accent":   NEON_CYAN,
        "image":    SCREENSHOT_FILES["offers"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul booking curve analyzer slouží k analýze vývoje "
                    "nabídkové ceny letenky v závislosti na předstihu nákupu. "
                    "Každá barevná křivka ve výstupním grafu odpovídá jednomu "
                    "konkrétnímu dni odletu. Osa X znázorňuje datum sběru dat, "
                    "osa Y nabídkovou cenu v amerických dolarech. Cílem modulu "
                    "je umožnit identifikaci okamžiku, ve kterém je nákup "
                    "letenky nejvýhodnější."
                )
            },
            {
                "heading": "ovládací prvky filtrového panelu",
                "body": (
                    "Levý postranní panel obsahuje filtr zrušených letů, "
                    "rozbalovací nabídku výchozí letiště, rozbalovací nabídku "
                    "destinace, rozbalovací nabídku datum odletu spoje a dvě "
                    "skupiny zaškrtávacích polí pro tradiční a nízkonákladové "
                    "letecké společnosti. Filtr zrušených letů přepíná datový "
                    "rozsah mezi celým souborem a podmnožinou pouze "
                    "uskutečněných letů. Filtr datum odletu spoje umožňuje "
                    "izolovat jediný konkrétní den, což usnadňuje detailní "
                    "analýzu jednoho zvoleného letu."
                )
            },
            {
                "heading": "interpretace výstupu",
                "body": (
                    "Z grafického výstupu lze odvodit, jakým způsobem se cena "
                    "vyvíjí s blížícím se datem odletu. Stabilní cenové pásmo "
                    "v období září až listopad bývá zpravidla následováno "
                    "postupným nárůstem v prosinci a prudkým cenovým skokem "
                    "v posledních dnech před odletem. Modul umožňuje sledovat "
                    "tento jev odděleně pro jednotlivé letecké společnosti, "
                    "případně jej porovnávat napříč vybranými trasami."
                )
            },
            {
                "heading": "doporučený pracovní postup",
                "body": (
                    "Pro získání reprezentativního pohledu se doporučuje "
                    "ponechat datum odletu spoje na hodnotě vše a vybrat "
                    "konkrétní trasu prostřednictvím rozbalovacích nabídek "
                    "výchozí letiště a destinace. Pro detailní analýzu "
                    "jednoho dne odletu je následně možné vybrat tento den "
                    "z nabídky datum odletu spoje a zkoumat tvar rezervační "
                    "křivky pro vybranou aerolinii."
                )
            }
        ]
    },

    # =================================================================
    # 2. january flight tracker
    # =================================================================
    {
        "id":       "january",
        "title":    "Vizualizace cen letenek z Ledna",
        "subtitle": "porovnání cen letů v lednu 2026 napříč výchozími letišti",
        "accent":   NEON_PINK,
        "image":    SCREENSHOT_FILES["january"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul january flight tracker je určen pro paralelní "
                    "porovnání cen letenek na dvou nezávisle konfigurovaných "
                    "trasách. Výstupní graf zobrazuje denní vývoj cen pro "
                    "leden 2026, přičemž každá ze dvou linií odpovídá jednomu "
                    "trackeru. Tracker alfa je vykreslen tyrkysovou barvou, "
                    "tracker beta růžovou."
                )
            },
            {
                "heading": "konfigurace trackerů alfa a beta",
                "body": (
                    "Levý postranní panel je rozdělen na dva nezávislé bloky. "
                    "Každý blok obsahuje rozbalovací nabídku počáteční "
                    "letiště, rozbalovací nabídku destinace, zaškrtávací pole "
                    "pro výběr měsíců a dvě skupiny zaškrtávacích polí pro "
                    "tradiční a nízkonákladové letecké společnosti. "
                    "Konfigurace obou trackerů je nezávislá, čímž je umožněno "
                    "porovnání libovolné dvojice tras nebo srovnání téže "
                    "trasy mezi dvěma odlišnými skupinami leteckých "
                    "společností."
                )
            },
            {
                "heading": "agregační metoda",
                "body": (
                    "V horní části panelu je umístěn přepínač agregační "
                    "metody mezi aritmetickým průměrem a mediánem. "
                    "Aritmetický průměr je citlivý na extrémní hodnoty a "
                    "vhodný pro souhrnný přehled. Medián je odolnější vůči "
                    "ojedinělým výkyvům a poskytuje robustnější obraz "
                    "středové hodnoty cen."
                )
            },
            {
                "heading": "filtr zrušených letů",
                "body": (
                    "Společný filtr zrušených letů umožňuje rozhodnout, zda "
                    "budou do výpočtu zahrnuty i lety označené v datovém "
                    "souboru jako zrušené. Volba pouze uskutečněné lety "
                    "zužuje analyzovaný soubor na lety, které byly skutečně "
                    "odlétnuty, a zvyšuje tak věrohodnost výsledné cenové "
                    "křivky."
                )
            }
        ]
    },

    # =================================================================
    # 3. emission intelligence
    # =================================================================
    {
        "id":       "emission",
        "title":    "Porovnání emisí leteckých společností",
        "subtitle": "analýza uhlíkové stopy jednotlivých letů",
        "accent":   NEON_GREEN,
        "image":    SCREENSHOT_FILES["emission"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul emission intelligence system je zaměřen na "
                    "analýzu emisí oxidu uhličitého spojených s jednotlivými "
                    "lety. Výstupní graf zobrazuje časový vývoj emisních "
                    "ukazatelů pro vybranou trasu a leteckou společnost "
                    "v průběhu ledna 2026. Hodnoty jsou uváděny pro každý "
                    "den odletu odděleně."
                )
            },
            {
                "heading": "tři režimy zobrazení emisí",
                "body": (
                    "Spodní lišta filtrů obsahuje přepínač výběr způsobu "
                    "vizualizace emisí se třemi režimy. Režim průměrné CO2 "
                    "v kilogramech za hodinu vyjadřuje hodinovou produkci "
                    "emisí motoru a je vhodný pro porovnání efektivity "
                    "jednotlivých typů letadel. Režim odhadované CO2 "
                    "v kilogramech za let agreguje celkovou emisní stopu "
                    "konkrétního letu. Režim emise na sedadlo přepočítává "
                    "hodinovou produkci na jedno sedadlo a poskytuje "
                    "nejkorektnější srovnání mezi letadly s odlišnou "
                    "kapacitou."
                )
            },
            {
                "heading": "filtry trasy a letecké společnosti",
                "body": (
                    "Spodní lišta dále obsahuje rozbalovací nabídku výchozí "
                    "letiště, rozbalovací nabídku destinace a rozbalovací "
                    "nabídku letecká společnost. Posledně jmenovaný filtr "
                    "se automaticky aktualizuje podle vybrané kombinace "
                    "trasy a nabízí pouze ty dopravce, kteří danou trasu "
                    "skutečně provozují."
                )
            },
            {
                "heading": "skupinování datových řad",
                "body": (
                    "Přepínač filtrovat data podle umožňuje rozdělit "
                    "datové řady ve výstupním grafu podle letecké "
                    "společnosti, podle typu letadla nebo podle trasy. "
                    "Skupinování podle typu letadla je vhodné při analýze "
                    "vlivu jednotlivých letadlových typů na emisní stopu, "
                    "skupinování podle letecké společnosti je užitečné při "
                    "porovnávání environmentální výkonnosti dopravců."
                )
            },
            {
                "heading": "souhrnná statistická lišta",
                "body": (
                    "Pod grafem je umístěna statistická lišta zobrazující "
                    "průměr, medián, minimum a maximum vybrané emisní "
                    "metriky spolu s počtem zpracovaných záznamů. Lišta "
                    "rovněž obsahuje souhrnné hodnoty pro každou "
                    "vykreslenou skupinu."
                )
            }
        ]
    },

    # =================================================================
    # 4. route sankey diagram
    # =================================================================
    {
        "id":       "sankey",
        "title":    "Porovnání ceny tras pomocí Sankey diagramu",
        "subtitle": "diagram cenových toků mezi letišti",
        "accent":   NEON_YELLOW,
        "image":    SCREENSHOT_FILES["sankey"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul route sankey diagram vizualizuje prostřednictvím "
                    "Sankeyova diagramu cenové toky mezi pěti výchozími "
                    "letišti a čtyřmi cílovými destinacemi. Šířka spojení "
                    "mezi uzly je úměrná průměrné nebo mediánové ceně "
                    "letenky na dané trase. Diagram tak na jediném pohledu "
                    "umožňuje identifikovat trasy s nadprůměrnou cenovou "
                    "hladinou i trasy s cenami pod průměrem."
                )
            },
            {
                "heading": "filtry výchozího letiště a destinace",
                "body": (
                    "Spodní lišta obsahuje rozbalovací nabídku výchozí "
                    "letiště a rozbalovací nabídku destinace s možností "
                    "vícenásobného výběru. Volbou všechna výchozí letiště "
                    "a všechny destinace je zobrazen kompletní diagram, "
                    "zúžením výběru lze izolovat dílčí skupiny tras "
                    "vhodné pro detailnější srovnání."
                )
            },
            {
                "heading": "přepínač statistické metody",
                "body": (
                    "Přepínač price statistic umožňuje volbu mezi "
                    "aritmetickým průměrem a mediánem ceny. Při zvolení "
                    "aritmetického průměru jsou spojení vykreslena "
                    "tyrkysovým odstínem, při zvolení mediánu odstínem "
                    "růžovým. Rozdíl mezi oběma metrikami je informativní "
                    "z hlediska identifikace tras s vysokou cenovou "
                    "rozptyleností."
                )
            },
            {
                "heading": "spodní statistická lišta",
                "body": (
                    "Pod diagramem je umístěn pruh se souhrnnými "
                    "statistikami pro každou trasu. Pro každou kombinaci "
                    "výchozího letiště a destinace jsou uvedeny průměrná "
                    "cena, mediánová cena, rozdíl mezi oběma hodnotami a "
                    "celkový počet záznamů. Kladná hodnota rozdílu "
                    "naznačuje přítomnost extrémně vysokých cen, které "
                    "posouvají aritmetický průměr nad medián."
                )
            }
        ]
    },

    # =================================================================
    # 5. gini analyzer
    # =================================================================
    {
        "id":       "gini",
        "title":    "Analyzátor Gini nerovnosti",
        "subtitle": "analyzátor cenové nerovnosti napříč trasami",
        "accent":   NEON_PURPLE,
        "image":    SCREENSHOT_FILES["gini"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul gini analyzer slouží k vyhodnocení míry cenové "
                    "nerovnoměrnosti na sledovaných trasách. Výpočet "
                    "vychází z definice koeficientu true gini podle Santos "
                    "a Dias (2024), kde hodnota 0 odpovídá dokonalé cenové "
                    "rovnosti a hodnota blížící se 1 maximální nerovnosti. "
                    "Modul umožňuje tři odlišné režimy zobrazení."
                )
            },
            {
                "heading": "režim lorenzova křivka",
                "body": (
                    "Režim lorenz vykresluje pro vybranou trasu Lorenzovu "
                    "křivku znázorňující kumulativní podíl populace letů "
                    "proti kumulativnímu podílu cen. Plocha mezi linií "
                    "rovnosti a samotnou křivkou je úměrná hodnotě "
                    "Giniho koeficientu. Anotace v levém horním rohu "
                    "uvádí přesnou hodnotu koeficientu, počet pozorování, "
                    "aritmetický průměr a medián cen na vybrané trase."
                )
            },
            {
                "heading": "režim sloupcový graf",
                "body": (
                    "Režim sloupcový vykresluje horizontální sloupcový "
                    "graf seřazený sestupně podle hodnoty true gini "
                    "koeficientu napříč všemi sledovanými trasami. "
                    "Referenční svislé čáry vyznačují tři pásma "
                    "interpretace: nízkou nerovnost (0,2), střední "
                    "nerovnost (0,3) a vysokou nerovnost (0,4). Tento "
                    "režim je vhodný pro identifikaci tras s nejvyšší "
                    "cenovou rozptyleností."
                )
            },
            {
                "heading": "režim heatmapa",
                "body": (
                    "Režim heatmap zobrazuje matici hodnot true gini "
                    "koeficientu, kde řádky odpovídají výchozím letištím "
                    "a sloupce jednotlivým destinacím. Barva každé buňky "
                    "vyjadřuje míru cenové nerovnosti na příslušné trase. "
                    "Tento režim umožňuje rychlé vizuální zhodnocení "
                    "celkové struktury nerovnosti napříč sledovanou sítí."
                )
            },
            {
                "heading": "filtr rozsah dat",
                "body": (
                    "Přepínač rozsah dat určuje, zda se do výpočtu "
                    "zahrnují i zrušené lety, nebo zda jsou uvažovány "
                    "pouze lety uskutečněné. Volba pouze uskutečněné lety "
                    "poskytuje konzervativnější odhad nerovnosti, neboť "
                    "vylučuje záznamy, které nebyly fakticky realizovány."
                )
            }
        ]
    },

    # =================================================================
    # 6. routes overview
    # =================================================================
    {
        "id":       "routes",
        "title":    "Příme porovnání leteckých linek",
        "subtitle": "přehled všech sledovaných tras a jejich cenových úrovní",
        "accent":   NEON_ORANGE,
        "image":    SCREENSHOT_FILES["routes"],
        "blocks": [
            {
                "heading": "účel modulu",
                "body": (
                    "Modul routes overview poskytuje souhrnný analytický "
                    "pohled na cenové úrovně všech dvaceti sledovaných "
                    "tras. Výstupní rozhraní obsahuje tři horizontální "
                    "sloupcové grafy umístěné vedle sebe: deset "
                    "nejlevnějších leteckých linek, deset nejdražších "
                    "leteckých linek a porovnání cenových úrovní výchozích "
                    "letišť bez ohledu na konkrétní destinaci."
                )
            },
            {
                "heading": "ovládací prvky systémových parametrů",
                "body": (
                    "Horní lišta obsahuje přepínač filtr zrušených letů s "
                    "možnostmi zahrnout i zrušené lety nebo pouze "
                    "uskutečněné lety, a dále přepínač agregační metoda "
                    "umožňující volbu mezi aritmetickým průměrem a "
                    "mediánem. Změna kteréhokoliv z těchto parametrů "
                    "okamžitě aktualizuje všechny tři grafy zobrazené "
                    "v dolní části rozhraní."
                )
            },
            {
                "heading": "filtry destinací",
                "body": (
                    "Nad každým grafem je samostatná skupina zaškrtávacích "
                    "polí umožňující selektivní zahrnutí nebo vyloučení "
                    "jednotlivých destinací. Filtry destinací jsou pro "
                    "každý ze tří grafů nezávislé, což umožňuje současně "
                    "zobrazit například nejlevnější trasy do všech "
                    "destinací a nejdražší trasy zúžené pouze na jednu "
                    "vybranou destinaci."
                )
            },
            {
                "heading": "interpretace dílčích grafů",
                "body": (
                    "Levý graf zobrazuje deset leteckých linek s nejnižší "
                    "agregovanou cenou v sestupném pořadí, prostřední "
                    "graf zobrazuje deset linek s nejvyšší agregovanou "
                    "cenou. Pravý graf agreguje hodnoty bez ohledu na "
                    "destinaci a slouží k porovnání průměrných cenových "
                    "úrovní mezi pěti výchozími letišti. Nejvyšší "
                    "průměrná cena za výchozí letiště zpravidla "
                    "odpovídá kombinaci slabší konkurence "
                    "nízkonákladových dopravců a vyšší míry tradičních "
                    "leteckých společností."
                )
            }
        ]
    }
]


# =====================================================================
# 5. styly opakovaně používaných prvků
# =====================================================================
NAV_BUTTON_STYLE_BASE = {
    "display":         "inline-block",
    "padding":         "10px 16px",
    "marginRight":     "8px",
    "marginBottom":    "8px",
    "color":           TEXT_MUTED,
    "backgroundColor": KPI_BG,
    "border":          f"1px solid {NEON_BLUE}40",
    "borderRadius":    "6px",
    "fontSize":        "11px",
    "letterSpacing":   "2px",
    "fontFamily":      "Courier New, monospace",
    "cursor":          "pointer",
    "textAlign":       "center",
    "minWidth":        "180px"
}

BLOCK_HEADING_STYLE = {
    "fontSize":      "13px",
    "letterSpacing": "2px",
    "fontFamily":    "Courier New, monospace",
    "fontWeight":    "bold",
    "marginTop":     "0px",
    "marginBottom":  "8px",
    "textTransform": "uppercase"
}

BLOCK_BODY_STYLE = {
    "color":         TEXT_MUTED,
    "fontSize":      "13px",
    "lineHeight":    "1.7",
    "fontFamily":    "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "marginBottom":  "10px",
    "textAlign":     "justify"
}


# =====================================================================
# 6. sestavení tabulky letišť (pro úvodní podstránku)
# =====================================================================
def _build_airport_card(code, name, accent):
    """sestaví jednu kartu s kódem letiště a jeho názvem."""
    return html.Div([
        html.Div(code, style={
            "color":         accent,
            "fontSize":      "20px",
            "fontWeight":    "bold",
            "fontFamily":    "Courier New, monospace",
            "letterSpacing": "3px",
            "textShadow":    f"0 0 8px {accent}80",
            "marginBottom":  "4px"
        }),
        html.Div(name, style={
            "color":      TEXT_MUTED,
            "fontSize":   "12px",
            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        })
    ], style={
        "padding":         "14px 18px",
        "backgroundColor": PANEL_BG,
        "border":          f"1px solid {accent}40",
        "borderRadius":    "8px",
        "minWidth":        "150px",
        "textAlign":       "center",
        "boxShadow":       f"0 0 10px {accent}20"
    })


def _build_airport_grid(airports, accent):
    """sestaví mřížku karet letišť."""
    return html.Div(
        [_build_airport_card(code, name, accent) for code, name in airports],
        style={
            "display":        "flex",
            "flexWrap":       "wrap",
            "gap":            "12px",
            "justifyContent": "center",
            "marginTop":      "14px",
            "marginBottom":   "20px"
        }
    )


def _build_module_quicklink(page):
    """sestaví dlaždici s odkazem na konkrétní modul manuálu."""
    accent = page["accent"]
    return html.Div([
        html.Div(page["title"].upper(), style={
            "color":         accent,
            "fontSize":      "12px",
            "letterSpacing": "2px",
            "fontFamily":    "Courier New, monospace",
            "fontWeight":    "bold",
            "textShadow":    f"0 0 6px {accent}80",
            "marginBottom":  "6px"
        }),
        html.Div(page["subtitle"], style={
            "color":      TEXT_MUTED,
            "fontSize":   "11px",
            "lineHeight": "1.5",
            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        })
    ], style={
        "padding":         "14px 16px",
        "backgroundColor": KPI_BG,
        "border":          f"1px solid {accent}40",
        "borderLeft":      f"3px solid {accent}",
        "borderRadius":    "0 8px 8px 0",
        "flex":            "1 1 280px",
        "minWidth":        "280px"
    })


def _build_overview_body():
    """sestaví obsah úvodní podstránky se seznamem letišť a moduly."""
    accent = NEON_BLUE

    # záhlaví podstránky
    header = html.Div([
        html.Div(
            "PŘEHLED SLEDOVANÝCH TRAS",
            style={
                "color":         accent,
                "fontSize":      "20px",
                "letterSpacing": "5px",
                "fontFamily":    "Courier New, monospace",
                "fontWeight":    "bold",
                "textShadow":    f"0 0 12px {accent}",
                "marginBottom":  "6px",
                "textAlign":     "center"
            }
        ),
        html.Div(
            "úvodní rozcestník platformy a seznam sledovaných letišť",
            style={
                "color":         NEON_BLUE,
                "fontSize":      "11px",
                "letterSpacing": "2px",
                "fontFamily":    "Courier New, monospace",
                "textAlign":     "center",
                "marginBottom":  "24px"
            }
        )
    ])

    # úvodní popis platformy
    intro_block = html.Div([
        html.Div("o platformě", style={
            **BLOCK_HEADING_STYLE,
            "color":      accent,
            "textShadow": f"0 0 6px {accent}80"
        }),
        html.Div(
            "Platforma neural flight analytics je analytickou aplikací "
            "zaměřenou na sledování a vyhodnocení cen letenek z pěti "
            "středoevropských výchozích letišť do čtyř klíčových destinací. "
            "Sběr dat probíhá od září 2025 do ledna 2026 a obsahuje rovněž "
            "metainformace o emisích oxidu uhličitého a typech provozovaných "
            "letadel. Veškeré moduly platformy sdílejí jednotný datový "
            "podklad a čerpají z formulářových exportů uložených v souborech "
            "s příponou form.csv pro každé výchozí letiště.",
            style=BLOCK_BODY_STYLE
        )
    ], style={
        "padding":         "14px 20px",
        "marginBottom":    "16px",
        "backgroundColor": PANEL_BG,
        "borderLeft":      f"3px solid {accent}",
        "borderRadius":    "0 8px 8px 0"
    })

    # blok s výchozími letišti
    origins_block = html.Div([
        html.Div("výchozí letiště (origin)", style={
            **BLOCK_HEADING_STYLE,
            "color":      NEON_CYAN,
            "textShadow": f"0 0 6px {NEON_CYAN}80"
        }),
        html.Div(
            "Pět středoevropských výchozích letišť, ze kterých byl prováděn "
            "sběr cen letenek. Třípísmenné kódy odpovídají standardu "
            "Mezinárodní asociace leteckých dopravců (IATA) a jsou "
            "používány konzistentně napříč všemi vizualizačními moduly.",
            style=BLOCK_BODY_STYLE
        ),
        _build_airport_grid(ORIGIN_AIRPORTS, NEON_CYAN)
    ], style={
        "padding":         "14px 20px",
        "marginBottom":    "16px",
        "backgroundColor": PANEL_BG,
        "borderLeft":      f"3px solid {NEON_CYAN}",
        "borderRadius":    "0 8px 8px 0"
    })

    # blok s cílovými letišti
    destinations_block = html.Div([
        html.Div("cílové destinace (destination)", style={
            **BLOCK_HEADING_STYLE,
            "color":      NEON_PINK,
            "textShadow": f"0 0 6px {NEON_PINK}80"
        }),
        html.Div(
            "Čtyři klíčové cílové destinace pokrývající hlavní evropské "
            "ekonomické a turistické uzly. Kód LON zahrnuje všechna "
            "londýnská letiště společně, neboť jsou v rámci leteckého "
            "provozu obvykle vykazována jako jedna destinace.",
            style=BLOCK_BODY_STYLE
        ),
        _build_airport_grid(DESTINATION_AIRPORTS, NEON_PINK)
    ], style={
        "padding":         "14px 20px",
        "marginBottom":    "16px",
        "backgroundColor": PANEL_BG,
        "borderLeft":      f"3px solid {NEON_PINK}",
        "borderRadius":    "0 8px 8px 0"
    })

    # přehled struktury sledovaných tras
    structure_block = html.Div([
        html.Div("struktura sledovaných tras", style={
            **BLOCK_HEADING_STYLE,
            "color":      NEON_YELLOW,
            "textShadow": f"0 0 6px {NEON_YELLOW}80"
        }),
        html.Div(
            "Kombinací pěti výchozích letišť a čtyř cílových destinací "
            "vzniká celkem dvacet sledovaných tras. Každá trasa je "
            "monitorována nezávisle a obsahuje záznamy nejen o ceně "
            "letenky, ale rovněž o letecké společnosti, typu letadla, "
            "plánovaném datu a čase odletu, době letu a stavu letu. "
            "Stav letu rozlišuje, zda byl daný let skutečně odlétnut, "
            "nebo zda došlo k jeho zrušení, což je následně využíváno "
            "filtrem zrušených letů ve většině modulů.",
            style=BLOCK_BODY_STYLE
        )
    ], style={
        "padding":         "14px 20px",
        "marginBottom":    "16px",
        "backgroundColor": PANEL_BG,
        "borderLeft":      f"3px solid {NEON_YELLOW}",
        "borderRadius":    "0 8px 8px 0"
    })

    # rozcestník na jednotlivé moduly
    module_pages = [p for p in PAGES_CONTENT if not p.get("is_overview")]
    modules_block = html.Div([
        html.Div("dostupné vizualizační moduly", style={
            **BLOCK_HEADING_STYLE,
            "color":      NEON_GREEN,
            "textShadow": f"0 0 6px {NEON_GREEN}80"
        }),
        html.Div(
            "Platforma obsahuje šest vzájemně propojených vizualizačních "
            "modulů, z nichž každý zpřístupňuje odlišný analytický pohled "
            "na zpracovaná data. Detailní popis funkcionality každého "
            "modulu je k dispozici na příslušné podstránce manuálu, kterou "
            "lze otevřít prostřednictvím horní navigační lišty.",
            style=BLOCK_BODY_STYLE
        ),
        html.Div(
            [_build_module_quicklink(p) for p in module_pages],
            style={
                "display":        "flex",
                "flexWrap":       "wrap",
                "gap":            "10px",
                "marginTop":      "14px"
            }
        )
    ], style={
        "padding":         "14px 20px",
        "marginBottom":    "12px",
        "backgroundColor": PANEL_BG,
        "borderLeft":      f"3px solid {NEON_GREEN}",
        "borderRadius":    "0 8px 8px 0"
    })

    return html.Div([
        header,
        html.Div([
            intro_block,
            origins_block,
            destinations_block,
            structure_block,
            modules_block
        ], style={"maxWidth": "1100px", "margin": "0 auto"})
    ])


# =====================================================================
# 7. sestavení obsahu jedné podstránky (modulové)
# =====================================================================
def _build_page_body(page):
    """sestaví tělo podstránky manuálu pro vybraný modul."""
    # speciální případ — úvodní rozcestník
    if page.get("is_overview"):
        return _build_overview_body()

    accent = page["accent"]
    img_src = _encode_image(page["image"]) if page.get("image") else None

    # nadpis a podtitulek podstránky
    header = html.Div([
        html.Div(
            page["title"].upper(),
            style={
                "color":         accent,
                "fontSize":      "20px",
                "letterSpacing": "5px",
                "fontFamily":    "Courier New, monospace",
                "fontWeight":    "bold",
                "textShadow":    f"0 0 12px {accent}",
                "marginBottom":  "6px",
                "textAlign":     "center"
            }
        ),
        html.Div(
            page["subtitle"],
            style={
                "color":         NEON_BLUE,
                "fontSize":      "11px",
                "letterSpacing": "2px",
                "fontFamily":    "Courier New, monospace",
                "textAlign":     "center",
                "marginBottom":  "20px"
            }
        )
    ])

    # blok s náhledovým snímkem
    if img_src:
        screenshot_block = html.Div([
            html.Img(
                src=img_src,
                style={
                    "width":         "100%",
                    "maxWidth":      "1100px",
                    "borderRadius":  "10px",
                    "border":        f"1px solid {accent}40",
                    "boxShadow":     f"0 0 24px {accent}30",
                    "display":       "block",
                    "margin":        "0 auto"
                }
            )
        ], style={
            "marginBottom": "24px",
            "padding":      "12px",
            "backgroundColor": KPI_BG,
            "borderRadius": "12px",
            "border":       f"1px solid {accent}20"
        })
    else:
        screenshot_block = html.Div(
            "náhledový snímek není v aktuálním nasazení k dispozici",
            style={
                "color":         TEXT_MUTED,
                "fontSize":      "11px",
                "fontStyle":     "italic",
                "textAlign":     "center",
                "padding":       "40px",
                "backgroundColor": KPI_BG,
                "border":        f"1px dashed {NEON_BLUE}40",
                "borderRadius":  "10px",
                "marginBottom":  "24px"
            }
        )

    # textové bloky s popisem funkcionality
    text_blocks = []
    for block in page["blocks"]:
        text_blocks.append(html.Div([
            html.Div(block["heading"], style={
                **BLOCK_HEADING_STYLE,
                "color":      accent,
                "textShadow": f"0 0 6px {accent}80"
            }),
            html.Div(block["body"], style=BLOCK_BODY_STYLE)
        ], style={
            "padding":         "14px 20px",
            "marginBottom":    "12px",
            "backgroundColor": PANEL_BG,
            "borderLeft":      f"3px solid {accent}",
            "borderRadius":    "0 8px 8px 0"
        }))

    return html.Div([
        header,
        screenshot_block,
        html.Div(text_blocks, style={"maxWidth": "1100px", "margin": "0 auto"})
    ])


# =====================================================================
# 8. sestavení navigačního panelu mezi podstránkami
# =====================================================================
def _build_nav_buttons(active_id):
    """sestaví seznam tlačítek navigační lišty."""
    buttons = []
    for page in PAGES_CONTENT:
        is_active = (page["id"] == active_id)
        accent    = page["accent"]

        if is_active:
            style = {
                **NAV_BUTTON_STYLE_BASE,
                "color":      accent,
                "border":     f"1px solid {accent}",
                "boxShadow":  f"0 0 12px {accent}60",
                "fontWeight": "bold"
            }
        else:
            style = NAV_BUTTON_STYLE_BASE

        buttons.append(html.Button(
            page["title"],
            id={"type": "manual-nav", "page": page["id"]},
            n_clicks=0,
            style=style
        ))

    return buttons


# =====================================================================
# 9. hlavní layout stránky manuálu
#    POZN.: navigační tlačítka i obsah úvodní podstránky jsou vykresleny
#    přímo v layoutu (nikoliv až callbackem), aby cílové komponenty
#    callbacku existovaly v DOMu hned po načtení stránky.
# =====================================================================
INITIAL_PAGE_ID = "overview"
INITIAL_PAGE = PAGES_CONTENT[0]

layout = html.Div([
    # tlačítko zpět na hlavní stránku
    html.Div([
        dcc.Link(
            "← zpět na hlavní stránku",
            href="/",
            style={
                "color":          NEON_PURPLE,
                "textDecoration": "none",
                "fontSize":       "11px",
                "letterSpacing":  "2px",
                "fontFamily":     "Courier New, monospace",
                "padding":        "8px 14px",
                "border":         f"1px solid {NEON_PURPLE}60",
                "borderRadius":   "6px",
                "display":        "inline-block"
            }
        )
    ], style={"marginBottom": "16px"}),

    # hlavní záhlaví manuálu
    html.Div([
        html.H1(
            "uživatelský manuál platformy",
            style={
                "color":         NEON_CYAN,
                "fontSize":      "26px",
                "letterSpacing": "6px",
                "textAlign":     "center",
                "fontFamily":    "Courier New, monospace",
                "textShadow":    f"0 0 14px {NEON_CYAN}",
                "marginBottom":  "6px"
            }
        ),
        html.Div(
            "neural flight analytics  ·  průvodce funkcemi vizualizačních modulů",
            style={
                "color":         NEON_BLUE,
                "fontSize":      "11px",
                "letterSpacing": "3px",
                "textAlign":     "center",
                "fontFamily":    "Courier New, monospace",
                "marginBottom":  "24px"
            }
        )
    ]),

    # navigační lišta — vykreslena STATICKY v layoutu (nikoliv callbackem)
    html.Div(
        _build_nav_buttons(INITIAL_PAGE_ID),
        id="manual-nav-container",
        style={
            "textAlign":       "center",
            "padding":         "16px 12px",
            "marginBottom":    "20px",
            "backgroundColor": PANEL_BG,
            "borderRadius":    "10px",
            "border":          f"1px solid {NEON_BLUE}30"
        }
    ),

    # tělo aktuální podstránky — naplněno hned počátečním obsahem
    html.Div(
        _build_page_body(INITIAL_PAGE),
        id="manual-page-body",
        style={"padding": "0 20px"}
    ),

    # zápatí
    html.Div([
        html.Hr(style={
            "border":    "none",
            "borderTop": f"1px solid {NEON_BLUE}30",
            "margin":    "40px 0 16px 0"
        }),
        html.Div(
            "neural flight analytics platform  ·  uživatelský manuál  ·  2026",
            style={
                "color":         TEXT_MUTED,
                "fontSize":      "10px",
                "letterSpacing": "2px",
                "textAlign":     "center",
                "fontFamily":    "Courier New, monospace",
                "opacity":       "0.6"
            }
        )
    ])
], style={
    "backgroundColor": BG_COLOR,
    "minHeight":       "100vh",
    "padding":         "20px 30px",
    "fontFamily":      "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "boxSizing":       "border-box"
})


# =====================================================================
# 10. callback pro přepínání podstránek
#     Používá pattern-matching ALL — callback se spustí při kliknutí
#     na kterékoliv tlačítko skupiny manual-nav. Tlačítka jsou v DOMu
#     vykreslena již v layoutu, takže callback má vždy dostupné vstupy.
# =====================================================================
@app.callback(
    Output("manual-nav-container", "children"),
    Output("manual-page-body",     "children"),
    Input({"type": "manual-nav", "page": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def switch_page(_n_clicks_list):
    """vykreslí navigaci a tělo podstránky podle stisknutého tlačítka."""
    triggered = callback_context.triggered

    # výchozí stav — pokud nebyl rozpoznán žádný stisk, ponechá se výchozí stránka
    if not triggered or triggered[0]["value"] in (None, 0):
        active_id = INITIAL_PAGE_ID
    else:
        # identifikátor má tvar JSON: {"page":"emission","type":"manual-nav"}.n_clicks
        prop_id = triggered[0]["prop_id"]
        active_id = INITIAL_PAGE_ID
        for page in PAGES_CONTENT:
            if f'"page":"{page["id"]}"' in prop_id:
                active_id = page["id"]
                break

    # nalezení odpovídající stránky
    page = next(
        (p for p in PAGES_CONTENT if p["id"] == active_id),
        PAGES_CONTENT[0]
    )

    return _build_nav_buttons(active_id), _build_page_body(page)


# =====================================================================
# 11. vstupní bod pro lokální vývoj
# =====================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8090))
    app.run(host="0.0.0.0", port=port, debug=False)
