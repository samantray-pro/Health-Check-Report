import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("health_tracker.db")

def init_db():
    """Initializes the local SQLite database schema and indexes."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 1. Persona Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            health_issues TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Uploaded Source Reports Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            report_date DATE,
            panel_count INTEGER DEFAULT 0,
            parameter_count INTEGER DEFAULT 0,
            extracted_raw_text TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)

        # 3. Individual Medical Test Records Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            report_id INTEGER,
            test_name TEXT NOT NULL,
            raw_test_name TEXT,
            panel TEXT,
            category TEXT,
            value REAL NOT NULL,
            value_str TEXT,
            unit TEXT,
            reference_range TEXT,
            flag TEXT DEFAULT 'NORMAL',
            test_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE SET NULL
        );
        """)

        # Migrations: Ensure newly added columns exist in existing SQLite databases
        reports_cols = [row[1] for row in cursor.execute("PRAGMA table_info(reports)").fetchall()]
        if "panel_count" not in reports_cols:
            cursor.execute("ALTER TABLE reports ADD COLUMN panel_count INTEGER DEFAULT 0;")
        if "parameter_count" not in reports_cols:
            cursor.execute("ALTER TABLE reports ADD COLUMN parameter_count INTEGER DEFAULT 0;")

        records_cols = [row[1] for row in cursor.execute("PRAGMA table_info(test_records)").fetchall()]
        if "panel" not in records_cols:
            cursor.execute("ALTER TABLE test_records ADD COLUMN panel TEXT;")
        if "category" not in records_cols:
            cursor.execute("ALTER TABLE test_records ADD COLUMN category TEXT;")

        # Performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_profile_test ON test_records (profile_id, test_name, test_date ASC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_profile_panel ON test_records (profile_id, panel);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_test_date ON test_records (test_date);")
        conn.commit()

    backfill_panels_and_categories()
    recalculate_all_flags()

def backfill_panels_and_categories():
    """Backfills panel and category columns for any legacy records missing them."""
    from app.parser import get_test_panel, get_test_category

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        records = cur.execute("SELECT id, test_name, panel, category FROM test_records WHERE panel IS NULL OR category IS NULL").fetchall()
        for r in records:
            c = r["category"] or get_test_category(r["test_name"])
            p = r["panel"] or get_test_panel(r["test_name"], c)
            cur.execute("UPDATE test_records SET panel = ?, category = ? WHERE id = ?", (p, c, r["id"]))

        # Backfill reports panel_count and parameter_count
        cur.execute("""
            UPDATE reports
            SET parameter_count = (SELECT COUNT(*) FROM test_records WHERE test_records.report_id = reports.id),
                panel_count = (SELECT COUNT(DISTINCT panel) FROM test_records WHERE test_records.report_id = reports.id)
            WHERE parameter_count = 0 OR panel_count = 0
        """)
        conn.commit()

def recalculate_all_flags():
    """Recalculates clinical flags (HIGH, LOW, NORMAL) for all existing test records using reference ranges and biomarker dictionary."""
    import re
    from app.parser import determine_clinical_flag, SORTED_BIOMARKER_ALIASES

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        records = cur.execute("SELECT id, test_name, value, reference_range, flag FROM test_records").fetchall()
        for r in records:
            dict_meta = None
            norm_name = re.sub(r'[^a-z0-9]', '', r["test_name"].lower())
            for alias, meta in SORTED_BIOMARKER_ALIASES:
                alias_norm = re.sub(r'[^a-z0-9]', '', alias)
                if norm_name == alias_norm or re.search(r'\b' + re.escape(alias) + r'\b', r["test_name"].lower()):
                    dict_meta = meta
                    break

            computed_flag = determine_clinical_flag(r["value"], r["reference_range"], dict_meta)
            if computed_flag != r["flag"]:
                cur.execute("UPDATE test_records SET flag = ? WHERE id = ?", (computed_flag, r["id"]))

        conn.commit()

@contextmanager
def get_db():
    """Context manager for thread-safe SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def seed_sample_data_if_empty():
    """No-op: sample data seeding disabled to ensure clean, user-owned local database."""
    pass

