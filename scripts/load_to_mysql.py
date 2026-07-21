"""
load_to_mysql.py
==================
Purpose: Load the cleaned, anonymized CSV into our MySQL database
(upi_spend_insights) so we can query it from MySQL Workbench.

Concepts used:
- mysql.connector: Python's library for talking to a MySQL server
- getpass: lets us type a password without it being visible or saved in code
- SQL CREATE TABLE: defines the structure (columns + types) before inserting data
"""

import pandas as pd
import mysql.connector
from getpass import getpass

# ---------------------------------------------------------
# STEP 1: Load the safe, anonymized CSV
# ---------------------------------------------------------
df = pd.read_csv("data/processed/upi_transactions_anonymized.csv")
df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
print(f"Loaded {len(df)} rows from CSV")


# ---------------------------------------------------------
# STEP 2: Connect to MySQL
# ---------------------------------------------------------
# getpass() shows a hidden prompt in the terminal - safer than typing
# your password directly into the script where it could get committed to GitHub
password = getpass("Enter your MySQL root password: ")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=password,
    database="upi_spend_insights"
)
cursor = conn.cursor()
print("Connected to MySQL")


# ---------------------------------------------------------
# STEP 3: Create the transactions table (defines column names + types)
# ---------------------------------------------------------
# DROP TABLE IF EXISTS lets us safely re-run this script without errors
cursor.execute("DROP TABLE IF EXISTS transactions")

cursor.execute("""
    CREATE TABLE transactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,
        time VARCHAR(20),
        category VARCHAR(50),
        type VARCHAR(10),
        amount DECIMAL(10, 2),
        counterparty VARCHAR(100),
        month VARCHAR(7)
    )
""")
print("Table 'transactions' created")


# ---------------------------------------------------------
# STEP 4: Insert each row from the DataFrame into the table
# ---------------------------------------------------------
insert_query = """
    INSERT INTO transactions (date, time, category, type, amount, counterparty, month)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# df.itertuples() loops through each row of the DataFrame one at a time
rows_inserted = 0
for row in df.itertuples(index=False):
    cursor.execute(insert_query, (
        row.date, row.time, row.category, row.type,
        row.amount, row.counterparty, row.month
    ))
    rows_inserted += 1

conn.commit()  # commit() saves all the inserted rows permanently
print(f"Inserted {rows_inserted} rows")


# ---------------------------------------------------------
# STEP 5: Quick sanity check
# ---------------------------------------------------------
cursor.execute("SELECT COUNT(*) FROM transactions")
count = cursor.fetchone()[0]
print(f"Total rows in table now: {count}")

cursor.close()
conn.close()
print("Done - check MySQL Workbench, database: upi_spend_insights, table: transactions")