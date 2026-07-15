"""
clean_and_anonymize.py
========================
Purpose: Take the raw parsed transaction data (which still has sensitive
info like transaction IDs and real names) and turn it into a safe,
categorized dataset that we can commit to GitHub.

Concepts used:
- functions: reusable blocks of code (def some_name(...): ...)
- dictionaries: key -> value lookup tables (like a phone book)
- pandas .apply(): runs a function on every row of a column
"""

import re
import pandas as pd

# ---------------------------------------------------------
# STEP 1: Load the raw parsed data (created by extract_transactions.py)
# ---------------------------------------------------------
df = pd.read_csv("data/processed/phonepe_raw_parsed.csv")
print(f"Loaded {len(df)} transactions")


# ---------------------------------------------------------
# STEP 2: Categorize each transaction based on keywords in the description
# ---------------------------------------------------------
def categorize(description, txn_type):
    """
    Looks at the description text and returns a category label.
    'description.lower()' converts text to lowercase so matching
    isn't case-sensitive (e.g. "Zomato" and "zomato" both match).
    """
    d = description.lower()

    if "money added to upi lite" in d:
        return "UPI Lite Top-up"
    if any(keyword in d for keyword in ["recharge", "jio", "airtel", " vi "]):
        return "Recharge"
    if any(keyword in d for keyword in ["flipkart", "amazon", "myntra"]):
        return "Shopping"
    if any(keyword in d for keyword in ["institute", "university", "college", "school"]):
        return "Education/Fees"
    if any(keyword in d for keyword in ["electricity", "water bill", "gas", "broadband", "dth"]):
        return "Utilities/Bills"
    if any(keyword in d for keyword in ["zomato", "swiggy", "restaurant", "food", "cafe", "hotel"]):
        return "Food & Dining"
    if any(keyword in d for keyword in ["petrol", "fuel", "uber", "ola", "irctc", "redbus"]):
        return "Transport"
    if txn_type == "Credit" and "received from" in d:
        return "Money Received"
    if txn_type == "Debit" and "paid to" in d:
        return "Person/Merchant Payment"
    return "Others"

# .apply() runs the categorize() function on every row.
# axis=1 means "process row by row" (not column by column).
df["category"] = df.apply(lambda row: categorize(row["description"], row["type"]), axis=1)


# ---------------------------------------------------------
# STEP 3: Pull out just the name/merchant from the description text
# ---------------------------------------------------------
def extract_name(description):
    """Strips 'Paid to ' or 'Received from ' to leave just the name."""
    d = description.strip()
    for prefix in ["Paid to ", "Received from "]:
        if d.startswith(prefix):
            return d[len(prefix):].strip()
    return d

df["counterparty"] = df["description"].apply(extract_name)


# ---------------------------------------------------------
# STEP 4: Anonymize individual people, but keep business names
# ---------------------------------------------------------
# Business names are safe to show (they're public companies, not private people)
known_merchants = [
    "flipkart", "amazon", "myntra", "zomato", "swiggy", "jio", "airtel",
    "irctc", "redbus", "uber", "ola", "netflix", "spotify", "google",
    "phonepe", "paytm", "bigbasket", "blinkit", "zepto", "dominos",
    "mcdonald", "starbucks", "indian oil", "bharat petroleum", "hp petrol",
]

def is_business(name):
    n = name.lower()
    return any(merchant in n for merchant in known_merchants)

# This dictionary remembers: "Rohit Sharma" -> "Person_1"
# so that if the same person appears again later, they get the SAME label
# (this keeps patterns visible, e.g. "Person_5 received money 10 times")
person_map = {}
next_number = [0]  # using a list so we can modify it inside the function below

def anonymize(name):
    if is_business(name):
        return name  # leave business names untouched
    if name not in person_map:
        next_number[0] += 1
        person_map[name] = f"Person_{next_number[0]}"
    return person_map[name]

df["counterparty"] = df["counterparty"].apply(anonymize)


# ---------------------------------------------------------
# STEP 5: Keep only the safe columns — drop transaction_id, utr_no, account
# ---------------------------------------------------------
safe_df = df[["date", "time", "category", "type", "amount", "counterparty"]].copy()

print(f"Anonymized {next_number[0]} unique individuals")
print(f"Final safe dataset has {len(safe_df)} rows and columns: {list(safe_df.columns)}")


# ---------------------------------------------------------
# STEP 6: Save the safe file — THIS is the one that goes to GitHub
# ---------------------------------------------------------
safe_df.to_csv("data/processed/upi_transactions_anonymized.csv", index=False)
print("Saved: data/processed/upi_transactions_anonymized.csv")
print(safe_df.head(10))