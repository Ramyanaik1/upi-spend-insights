"""
extract_transactions.py
========================
Purpose: Read a PhonePe transaction statement PDF and convert it into
a clean, structured CSV file that we can later load into SQL, Excel,
and Power BI.

Concepts used:
- pdfplumber: reads text out of a PDF file
- regex (re module): finds patterns of text (like "a date followed by an amount")
- pandas: organizes data into a table (like an Excel sheet) called a DataFrame
"""

import re                # regex library - built into Python, no install needed
import pdfplumber        # reads PDF files
import pandas as pd      # handles tabular data (rows & columns)

# ---------------------------------------------------------
# STEP 1: Open the PDF and pull out all the text, page by page
# ---------------------------------------------------------
# Change this path if your PDF is named differently or in a different folder
PDF_PATH = "data/raw/PhonePe_Transaction_Statements.pdf"

all_text = []  # empty list - we'll add each page's text into this

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages in PDF: {len(pdf.pages)}")
    for page in pdf.pages:
        text = page.extract_text()   # extract_text() pulls out plain text from one page
        if text:                      # sometimes a page might be blank, so we check
            all_text.append(text)

# Join all pages into one big block of text, separated by newlines
full_text = "\n".join(all_text)
print(f"Extracted {len(full_text)} characters of text.")


# ---------------------------------------------------------
# STEP 2: Remove header/footer lines that repeat on every page
# ---------------------------------------------------------
# These lines don't contain transaction data, so we filter them out
lines = full_text.split("\n")
clean_lines = []
for line in lines:
    if line.startswith("Transaction Statement for"):
        continue  # 'continue' skips this line and moves to the next one
    if line.strip() == "Date Transaction Details Type Amount":
        continue
    if line.startswith("This is a system generated statement"):
        continue
    if re.match(r"^Page \d+ of \d+", line):
        continue  # regex: matches lines like "Page 3 of 190"
    clean_lines.append(line)

clean_text = "\n".join(clean_lines)


# ---------------------------------------------------------
# STEP 3: Use regex to find every transaction block
# ---------------------------------------------------------
# A transaction in the text looks like this (spanning 4 lines):
#   Jan 01, 2025 Paid to XYZ Debit INR 180.00
#   08:03 AM Transaction ID : T2501011234567890
#   UTR No : 485039235068
#   Debited from XX9829
#
# The regex pattern below describes this exact shape so Python can find it.
# (?P<name>...) creates a "named group" so we can easily grab that piece later.

pattern = re.compile(
    r"(?P<date>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2}, \d{4}) "
    r"(?P<desc>.*?) "
    r"(?P<type>Debit|Credit) INR\s*(?P<amt1>[\d,]+\.\d{2})?\s*\n"
    r"(?P<time>\d{2}:\d{2} [AP]M) Transaction ID\s*:\s*(?P<txnid>\S+)\s*(?P<amt2>[\d,]+\.\d{2})?\s*\n"
    r"UTR No\s*:\s*(?P<utr>\d+)\s*\n"
    r"(?:Debited from|Credited to)\s*(?P<account>\S+)"
)

# finditer() scans through clean_text and returns every match it finds
records = []
for match in pattern.finditer(clean_text):
    data = match.groupdict()  # groupdict() turns the named groups into a dictionary

    # The amount sometimes appears right after the date, sometimes after
    # the Transaction ID (depends on how long the description text is).
    # We just take whichever one is not empty.
    amount = data["amt1"] or data["amt2"]

    records.append({
        "date": data["date"],
        "time": data["time"],
        "description": data["desc"].strip(),
        "type": data["type"],
        "amount": float(amount.replace(",", "")),
        "transaction_id": data["txnid"],
        "utr_no": data["utr"],
        "account": data["account"],
    })

print(f"Transactions found: {len(records)}")


# ---------------------------------------------------------
# STEP 4: Turn the list of records into a pandas DataFrame (a table)
# ---------------------------------------------------------
df = pd.DataFrame(records)

# Combine date + time into a proper datetime column, then sort chronologically
df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%b %d, %Y %I:%M %p")
df["date"] = pd.to_datetime(df["date"], format="%b %d, %Y").dt.date
df = df.sort_values("datetime").reset_index(drop=True)


# ---------------------------------------------------------
# STEP 5: Save the raw parsed data
# ---------------------------------------------------------
# This file still has sensitive info (transaction IDs, account numbers)
# so it stays local - it will NOT be uploaded to GitHub.
df.to_csv("data/processed/phonepe_raw_parsed.csv", index=False)
print("Saved: data/processed/phonepe_raw_parsed.csv")
print(df.head())