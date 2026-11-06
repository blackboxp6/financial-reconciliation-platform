
import pandas as pd
import numpy as np
from pathlib import Path

# Reproducibility
np.random.seed(42)

# Configuration
NUM_TRANSACTIONS = 10_000

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Reference data
transaction_types = [
    "TRANSFER",
    "WITHDRAWAL",
    "DEPOSIT",
    "PAYMENT",
    "BILL_PAYMENT"
]

channels = [
    "MOBILE",
    "ONLINE",
    "ATM",
    "BRANCH",
    "POS"
]

# Generate bank transactions
bank_ids = [
    f"TXN{i:07d}"
    for i in range(1, NUM_TRANSACTIONS + 1)
]

dates = pd.to_datetime(
    np.random.choice(
        pd.date_range("2026-10-01", "2026-10-31"),
        NUM_TRANSACTIONS
    )
)

bank_df = pd.DataFrame({
    "transaction_id": bank_ids,
    "transaction_date": dates,
    "amount": np.round(
        np.random.uniform(100, 100000, NUM_TRANSACTIONS),
        2
    ),
    "transaction_type": np.random.choice(
        transaction_types, NUM_TRANSACTIONS
    ),
    "channel": np.random.choice(
        channels, NUM_TRANSACTIONS
    ),
    "currency": "PHP"
})

# Create gateway records from bank transactions
gateway_df = bank_df.copy()

# 1. Amount mismatches: 3%
amount_indices = np.random.choice(
    gateway_df.index,
    size=300,
    replace=False
)

gateway_df.loc[amount_indices, "amount"] *= 0.90

gateway_df["amount"] = gateway_df["amount"].round(2)

# 2. Date mismatches: 2%
date_indices = np.random.choice(
    gateway_df.index.difference(amount_indices),
    size=200,
    replace=False
)

gateway_df.loc[date_indices, "transaction_date"] += pd.Timedelta(days=1)

# 3. Missing from gateway: 2%
missing_gateway_indices = np.random.choice(
    gateway_df.index.difference(
        np.concatenate([amount_indices, date_indices])
    ),
    size=200,
    replace=False
)

gateway_df = gateway_df.drop(
    missing_gateway_indices
)

# 4. Missing from bank: 2%
missing_bank = bank_df.sample(
    n=200,
    random_state=100
).copy()

missing_bank["transaction_id"] = [
    f"EXT{i:07d}"
    for i in range(1, 201)
]

missing_bank["amount"] *= 1.05
missing_bank["amount"] = missing_bank["amount"].round(2)

gateway_df = pd.concat(
    [gateway_df, missing_bank],
    ignore_index=True
)

# 5. Duplicates: 1%
duplicates = gateway_df.sample(
    n=100,
    random_state=200
).copy()

gateway_df = pd.concat(
    [gateway_df, duplicates],
    ignore_index=True
)

# Shuffle records
bank_df = bank_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

gateway_df = gateway_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# Export datasets
bank_df.to_csv(
    DATA_DIR / "bank_transactions.csv",
    index=False
)

gateway_df.to_csv(
    DATA_DIR / "gateway_transactions.csv",
    index=False
)

print("DATA GENERATION COMPLETE")
print("------------------------")
print(f"Bank transactions: {len(bank_df):,}")
print(f"Gateway transactions: {len(gateway_df):,}")
print(f"Bank amount: PHP {bank_df['amount'].sum():,.2f}")
print(f"Gateway amount: PHP {gateway_df['amount'].sum():,.2f}")
