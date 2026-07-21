"""
load_to_sql.py
================
Purpose: Load the cleaned, anonymized CSV into a SQLite database so
we can run SQL queries on it.

Concepts used:
- sqlite3: Python's built-in library for talking to SQLite databases
- pandas .to_sql(): writes a DataFrame directly into a database table
"""

import sqlite3
import pandas as pd

# ---------------------------------------------------------
# STEP 1: Load the safe, anonymized CSV
# ---------------------------------------------------------
df = pd.read_csv("data/processed/upi_transactions_anonymized.csv")
print(f"Loaded {len(df)} rows from CSV")

# Add a 'month' column (YYYY-MM) - useful for month-wise SQL queries later
df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")


# ---------------------------------------------------------
# STEP 2: Connect to (or create) a SQLite database file
# ---------------------------------------------------------
# If 'upi_transactions.db' doesn't exist yet, this creates it.
conn = sqlite3.connect("sql/upi_transactions.db")


# ---------------------------------------------------------
# STEP 3: Write the DataFrame into a table called 'transactions'
# ---------------------------------------------------------
# if_exists="replace" means: if this table already exists, overwrite it
# (useful when we re-run this script after updating the data)
df.to_sql("transactions", conn, if_exists="replace", index=False)

print("Data loaded into sql/upi_transactions.db, table name: transactions")


# ---------------------------------------------------------
# STEP 4: Quick sanity check - run a test query
# ---------------------------------------------------------
result = pd.read_sql("SELECT COUNT(*) AS total_rows FROM transactions", conn)
print(result)

conn.close()