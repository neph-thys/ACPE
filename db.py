# db.py — database connection for ACPE
# Place this file in your PyCharm project root

import psycopg2
from psycopg2.extras import RealDictCursor

# Change these to match your PostgreSQL setup
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "acpe_db",
    "user":     "postgres",
    "password": "hello"
}

def get_connection():
    """Open and return a new database connection."""
    return psycopg2.connect(**DB_CONFIG)

def execute_query(sql, params=None, fetch=False):
    """
    Run any SQL statement.

    fetch=False  → INSERT / UPDATE / DELETE  (returns None)
    fetch=True   → SELECT                    (returns list of dicts)
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch:
                    return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# Quick connection test
if __name__ == "__main__":
    try:
        conn = get_connection()
        conn.close()
        print("Connected to acpe_db successfully.")
    except Exception as e:
        print(f"Connection failed: {e}")