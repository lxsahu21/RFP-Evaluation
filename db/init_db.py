"""
Creates rfp_eval.db (if not present) and seeds the default evaluation
criteria described in the project brief. Safe to re-run: seeding only
happens if the criteria table is empty.

Usage:
    python db/init_db.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "rfp_eval.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

DEFAULT_CRITERIA = [
    # name, description, weight, max_score, is_active
    ("Technical Capability", "Architecture, integrations, scalability, technical fit", 30, 10, 1),
    ("Implementation Plan", "Timeline, milestones, staffing, risk plan", 20, 10, 1),
    ("Commercial Value", "Pricing clarity, total cost, assumptions", 20, 10, 1),
    ("Security & Compliance", "Controls, certifications, privacy, auditability", 20, 10, 1),
    ("Support & Experience", "Support model, similar projects, references", 10, 10, 1),
]


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH, reseed: bool = False) -> None:
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn = get_connection(db_path)
    try:
        conn.executescript(schema)
        conn.commit()

        count = conn.execute("SELECT COUNT(*) AS c FROM evaluation_criteria").fetchone()["c"]
        if count == 0 or reseed:
            if reseed:
                conn.execute("DELETE FROM evaluation_criteria")
            conn.executemany(
                """
                INSERT INTO evaluation_criteria (name, description, weight, max_score, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                DEFAULT_CRITERIA,
            )
            conn.commit()
            print(f"Seeded {len(DEFAULT_CRITERIA)} evaluation criteria.")
        else:
            print("Criteria table already populated; skipping seed.")
    finally:
        conn.close()

    print(f"Database ready at: {os.path.abspath(db_path)}")


if __name__ == "__main__":
    init_db()
