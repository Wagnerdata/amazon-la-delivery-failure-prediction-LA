"""
run_eda.py — Load packages_validation.csv into SQLite and run EDA queries.

Usage:
    python sql/run_eda.py

Outputs:
    sql/packages.db       — SQLite database (overwritten each run)
    sql/eda_results.txt   — All query results as formatted text
"""

import re
import sqlite3
import textwrap
from pathlib import Path

import pandas as pd


# ── Paths ─────────────────────────────────────────────────────────────────────
SQL_DIR  = Path(__file__).parent
ROOT     = SQL_DIR.parent
CSV_PATH = ROOT / "data" / "packages_validation.csv"
DB_PATH  = SQL_DIR / "packages.db"
SQL_FILE = SQL_DIR / "eda_queries.sql"
OUT_FILE = SQL_DIR / "eda_results.txt"

TABLE    = "packages"


# ── Step 1: Load CSV → SQLite ─────────────────────────────────────────────────
def load_csv_to_sqlite(csv_path: Path, db_path: Path, table: str) -> int:
    """Read the CSV and write it to a fresh SQLite table. Returns row count."""
    df = pd.read_csv(csv_path)

    # Remove any stale database so we always start clean
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    df.to_sql(table, conn, index=False, if_exists="replace")
    conn.commit()
    conn.close()
    return len(df)


# ── Step 2: Parse SQL file into (label, sql) pairs ───────────────────────────
def parse_queries(sql_file: Path) -> list[tuple[str, str]]:
    """
    Split the SQL file into individual queries.
    Each query is preceded by a comment line starting with '-- N. Label'.
    Returns a list of (label, sql_statement) tuples.
    """
    raw = sql_file.read_text(encoding="utf-8")

    # Split on lines matching  -- N. Label  (number + dot + title)
    parts = re.split(r"\n(--\s+\d+\.\s+[^\n]+)\n", raw)

    queries = []
    i = 0
    # parts[0] is the file header block (before first numbered comment); skip it
    while i < len(parts):
        chunk = parts[i].strip()
        # A numbered label comment
        if re.match(r"^--\s+\d+\.", chunk):
            label = re.sub(r"^--\s+\d+\.\s*", "", chunk).strip()
            # The SQL body follows immediately
            sql_body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            # Strip any trailing file-level comments / blank lines
            sql_body = sql_body.split("\n\n")[0].strip()
            if sql_body:
                queries.append((label, sql_body))
            i += 2
        else:
            i += 1

    return queries


# ── Step 3: Execute a query and return a formatted string ─────────────────────
def run_query(conn: sqlite3.Connection, label: str, sql: str) -> str:
    """Run one SQL statement; return a nicely formatted result block."""
    cursor = conn.execute(sql)
    cols   = [desc[0] for desc in cursor.description]
    rows   = cursor.fetchall()

    # Build a simple fixed-width table
    col_widths = [len(c) for c in cols]
    str_rows = []
    for row in rows:
        str_row = [str(v) if v is not None else "NULL" for v in row]
        for j, val in enumerate(str_row):
            col_widths[j] = max(col_widths[j], len(val))
        str_rows.append(str_row)

    sep  = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    hdr  = "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols)) + " |"
    body = "\n".join(
        "| " + " | ".join(v.ljust(col_widths[j]) for j, v in enumerate(row)) + " |"
        for row in str_rows
    )

    table_str = "\n".join([sep, hdr, sep, body, sep]) if str_rows else "(no rows)"

    block = (
        f"\n{'='*60}\n"
        f"  {label}\n"
        f"{'='*60}\n"
        f"{table_str}\n"
    )
    return block


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    # 1. Load data
    print(f"Loading {CSV_PATH.name} → {DB_PATH.name}…")
    n_rows = load_csv_to_sqlite(CSV_PATH, DB_PATH, TABLE)
    print(f"  {n_rows:,} rows loaded into table '{TABLE}'")

    # 2. Parse queries
    queries = parse_queries(SQL_FILE)
    print(f"  {len(queries)} queries found in {SQL_FILE.name}\n")

    # 3. Run queries and collect output
    conn    = sqlite3.connect(DB_PATH)
    results = []

    for label, sql in queries:
        block = run_query(conn, label, sql)
        print(block)
        results.append(block)

    conn.close()

    # 4. Save all results to file
    header = (
        "EDA Results — Amazon LMRC Delivery Packages\n"
        f"Source : {CSV_PATH}\n"
        f"Rows   : {n_rows:,}\n"
        f"Queries: {len(queries)}\n"
    )
    OUT_FILE.write_text(header + "".join(results), encoding="utf-8")
    print(f"\nAll results saved → {OUT_FILE}")


if __name__ == "__main__":
    main()
