"""
Health Checkup Tracker - Database Manager
Utility to switch between clean GitHub distribution database and personal local database.
"""
import sys
import shutil
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent
MAIN_DB = ROOT_DIR / "health_tracker.db"
LOCAL_DB = ROOT_DIR / "health_tracker.local.db"

def print_status():
    print("=== Database Status ===")
    for name, path in [("Active DB (health_tracker.db)", MAIN_DB), ("Personal Local DB (health_tracker.local.db)", LOCAL_DB)]:
        if path.exists():
            try:
                conn = sqlite3.connect(path)
                cur = conn.cursor()
                profiles = cur.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
                records = cur.execute("SELECT COUNT(*) FROM test_records").fetchone()[0]
                reports = cur.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
                conn.close()
                print(f"[{name}]: {profiles} Profiles, {records} Test Records, {reports} Reports ({path.stat().st_size / 1024:.1f} KB)")
            except Exception as e:
                print(f"[{name}]: Error reading schema ({e})")
        else:
            print(f"[{name}]: (Not present)")

def backup_local():
    if not MAIN_DB.exists():
        print("Error: health_tracker.db not found.")
        return
    shutil.copy2(MAIN_DB, LOCAL_DB)
    print(f"Backed up active database -> {LOCAL_DB.name}")
    print_status()

def restore_local():
    if not LOCAL_DB.exists():
        print(f"Error: {LOCAL_DB.name} not found.")
        return
    shutil.copy2(LOCAL_DB, MAIN_DB)
    print(f"Restored personal records ({LOCAL_DB.name}) -> {MAIN_DB.name}")
    print_status()

def make_blank():
    from app.database import init_db
    if MAIN_DB.exists():
        # Auto-backup if it contains data before wiping
        conn = sqlite3.connect(MAIN_DB)
        records = conn.cursor().execute("SELECT COUNT(*) FROM test_records").fetchone()[0]
        conn.close()
        if records > 0:
            shutil.copy2(MAIN_DB, LOCAL_DB)
            print(f"Auto-saved existing records to {LOCAL_DB.name} before resetting.")
        MAIN_DB.unlink()
    
    init_db()
    print("Created fresh, blank health_tracker.db schema (0 records).")
    print_status()

if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print_status()
    elif cmd == "backup":
        backup_local()
    elif cmd == "restore":
        restore_local()
    elif cmd == "blank":
        make_blank()
    else:
        print("Usage: python manage_db.py [status | backup | restore | blank]")
