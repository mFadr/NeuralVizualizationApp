import os

# ── Change this one variable to switch environments ──────────────────
ENV = os.getenv("APP_ENV", "local")   # "local" or "cloud"

# ── Path definitions ─────────────────────────────────────────────────
BASE_PATHS = {
    "local": "C:/Users/mFadrhons/Documents/WS/repository/SAVE",
    "cloud": "/data/FORM"   # or wherever your cloud storage mounts
}

BASE = BASE_PATHS[ENV]

DATASET_PATHS = {
    'BER': f"{BASE}/FORM/BER_form.csv",
    'BUD': f"{BASE}/FORM/BUD_form.csv",
    'PRG': f"{BASE}/FORM/PRG_form.csv",
    'VIE': f"{BASE}/FORM/VIE_form.csv",
    'WAW': f"{BASE}/FORM/WAW_form.csv",
}

COM_PATHS = {
    'PRG': f"{BASE}/COM/PRG_com.csv",
    'WAW': f"{BASE}/COM/WAW_com.csv",
    'VIE': f"{BASE}/COM/VIE_com.csv",
}

OUTPUT_PATHS = {
    'PRG_form': f"{BASE}/FORM/PRG_form.csv",
    'WAW_form': f"{BASE}/FORM/WAW_form.csv",
    'VIE_form': f"{BASE}/FORM/VIE_form.csv",
    'BER_form': f"{BASE}/FORM/BER_form.csv",
    'BUD_form': f"{BASE}/FORM/BUD_form.csv",
}