"""
Modul pro sledování návštěvnosti a popularity podaplikací.
Ukládá data do SQLite databáze, případně PostgreSQL podle proměnné prostředí.

Pro DigitalOcean App Platform doporučeno:
- Pro testovací provoz: SQLite (data se ztratí při redeployi)
- Pro produkci: PostgreSQL přes proměnnou DATABASE_URL
"""

import os
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
from contextlib import contextmanager

# Cesta k databázi
DB_PATH = os.environ.get("ANALYTICS_DB_PATH", "/tmp/analytics.db")

# Zámek pro bezpečné zápisy ve více vláknech
_db_lock = Lock()


@contextmanager
def get_connection():
    """Bezpečné připojení k databázi s automatickým uzavřením."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Inicializace databáze. Volá se jednou při startu aplikace."""
    with _db_lock, get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_visits (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pathname    TEXT    NOT NULL,
                visited_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id  TEXT,
                user_agent  TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pathname
            ON page_visits(pathname)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_visited_at
            ON page_visits(visited_at)
        """)


def log_visit(pathname, session_id=None, user_agent=None):
    """Zaznamenání návštěvy stránky."""
    if not pathname:
        return
    try:
        with _db_lock, get_connection() as conn:
            conn.execute(
                "INSERT INTO page_visits (pathname, session_id, user_agent) "
                "VALUES (?, ?, ?)",
                (pathname, session_id, user_agent)
            )
    except Exception as e:
        # V produkci nechceme, aby chyba ve sledování shodila aplikaci
        print(f"[analytics] Chyba při ukládání návštěvy: {e}")


def get_stats():
    """Vrátí souhrnné statistiky pro hlavní stránku."""
    try:
        with get_connection() as conn:
            # Celkový počet návštěv
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM page_visits"
            ).fetchone()["c"]

            # Návštěvy za posledních 24 hodin
            since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            last_24h = conn.execute(
                "SELECT COUNT(*) AS c FROM page_visits WHERE visited_at >= ?",
                (since_24h,)
            ).fetchone()["c"]

            # Unikátní návštěvníci (podle session_id) za posledních 7 dní
            since_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
            unique_7d = conn.execute(
                "SELECT COUNT(DISTINCT session_id) AS c FROM page_visits "
                "WHERE visited_at >= ? AND session_id IS NOT NULL",
                (since_7d,)
            ).fetchone()["c"]

            # Popularita jednotlivých modulů
            module_rows = conn.execute("""
                SELECT pathname, COUNT(*) AS visits
                FROM page_visits
                WHERE pathname IN ('/offers', '/january', '/emission',
                                   '/sankey', '/gini', '/info', '/')
                GROUP BY pathname
                ORDER BY visits DESC
            """).fetchall()

            modules = [
                {"path": row["pathname"], "visits": row["visits"]}
                for row in module_rows
            ]

            return {
                "total":     total,
                "last_24h":  last_24h,
                "unique_7d": unique_7d,
                "modules":   modules,
            }
    except Exception as e:
        print(f"[analytics] Chyba při čtení statistik: {e}")
        return {
            "total":     0,
            "last_24h":  0,
            "unique_7d": 0,
            "modules":   [],
        }


# Mapování cest na čitelné názvy modulů
PATH_LABELS = {
    "/":         "HOME",
    "/offers":   "BOOKING CURVE",
    "/january":  "JANUARY TRACKER",
    "/emission": "EMISSION INTEL",
    "/sankey":   "ROUTE SANKEY",
    "/gini":     "GINI ANALYZER",
    "/info":     "MANUAL",
}
