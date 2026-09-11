"""
db_logger.py
============
Handles logging every search query (and its result) to MySQL.

Setup:
    pip install mysql-connector-python

Fill in your MySQL credentials below (DB_CONFIG), then make sure
you've already run schema.sql once to create the database + table.
"""

from datetime import datetime

import mysql.connector
from mysql.connector import Error

# ---------------------------------------------------------------------------
# EDIT THESE with your own MySQL credentials
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Gowrika@29",
    "database": "dance_search_db",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def extract_names(result: dict) -> str:
    """
    Reduce a search result down to just dance/folk names, comma-separated.
    (No 'type', 'category', or other structural keys — just the names.)
    """
    if result.get("type") == "dance":
        states = [s["state"] for s in result.get("states", [])]
        return ", ".join(states)

    if result.get("type") == "state":
        classical_names = result.get("classical", [])
        folk_names = [r["dance"] for r in result.get("folk", [])]
        return ", ".join(classical_names + folk_names)

    if result.get("type") == "suggestions":
        return ", ".join(result.get("dances", []))

    if result.get("type") in ("classical_list", "folk_list"):
        return ", ".join(d["dance"] for d in result.get("dances", []))

    return ""


def log_search(query: str, result: dict) -> None:
    """
    Insert one row into search_logs for this query.
    Never raises — logging should never break the actual search response.
    """
    now = datetime.now()
    names_only = extract_names(result)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO search_logs (query_searched, result, date, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (query, names_only, now.date(), now.time()),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        # Broad catch is intentional: logging must never break the actual
        # search response, regardless of what kind of DB error occurs.
        print(f"[db_logger] Failed to log search: {e}")