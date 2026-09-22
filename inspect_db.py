"""
Quick DB Inspector — Run this to see all data stored in the TechWing SQLite database.
Usage: python inspect_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'techwing_daily_log.db')

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    print(f"\nDatabase: {DB_PATH}")
    print(f"Size: {os.path.getsize(DB_PATH) / 1024:.1f} KB\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r['name'] for r in cur.fetchall()]
    print(f"Tables found: {tables}\n")
    print("=" * 70)

    for table in tables:
        cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        count = cur.fetchone()['cnt']
        print(f"\n[TABLE] {table.upper()}  ({count} records)")
        print("-" * 70)

        cur.execute(f"PRAGMA table_info({table})")
        cols = [r['name'] for r in cur.fetchall()]
        print(f"Columns: {', '.join(cols)}")

        if count == 0:
            print("  (no data yet)")
            continue

        cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 10")
        rows = cur.fetchall()
        for row in rows:
            print()
            for col in cols:
                val = row[col]
                if val and len(str(val)) > 80:
                    val = str(val)[:77] + "..."
                print(f"  {col:<20}: {val}")
        if count > 10:
            print(f"\n  ... and {count - 10} more records (showing latest 10)")

    conn.close()
    print("\n" + "=" * 70)
    print("Inspection complete.")

if __name__ == '__main__':
    inspect()
