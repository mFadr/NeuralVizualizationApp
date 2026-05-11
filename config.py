import os

ENV = os.getenv("APP_ENV", "local")



BASE = BASE_PATHS[ENV]

DATASET_PATHS = {
    'BER': f"{BASE}/FORM/BER_form.csv",
    'BUD': f"{BASE}/FORM/BUD_form.csv",
    'PRG': f"{BASE}/FORM/PRG_form.csv",
    'VIE': f"{BASE}/FORM/VIE_form.csv",
    'WAW': f"{BASE}/FORM/WAW_form.csv",
}

COM_PATHS = {
    'BER': f"{BASE}/FORM/BER_form.csv",
    'BUD': f"{BASE}/FORM/BUD_form.csv",
    'PRG': f"{BASE}/FORM/PRG_form.csv",
    'VIE': f"{BASE}/FORM/VIE_form.csv",
    'WAW': f"{BASE}/FORM/WAW_form.csv",
}

OUTPUT_PATHS = {
    'PRG_form': f"{BASE}/FORM/PRG_form.csv",
    'WAW_form': f"{BASE}/FORM/WAW_form.csv",
    'VIE_form': f"{BASE}/FORM/VIE_form.csv",
    'BER_form': f"{BASE}/FORM/BER_form.csv",
    'BUD_form': f"{BASE}/FORM/BUD_form.csv",
}

SCREENSHOT_FILES = {
    "offers":   f"{BASE}/FOTO/vizualizationFlightOffers.png",
    "january":  f"{BASE}/FOTO/vizualizationJanuary.png",
    "emission": f"{BASE}/FOTO/vizualizationEmision.png",
    "sankey":   f"{BASE}/FOTO/vizualizationSankey.png",
    "gini":     f"{BASE}/FOTO/vizualizationGini.png",
    "routes":   f"{BASE}/FOTO/route_overview.png",
    "map":      f"{BASE}/FOTO/map.png"
}
