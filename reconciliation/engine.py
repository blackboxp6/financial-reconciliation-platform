from reconciliation.fuzzy_matching import find_fuzzy_candidates
import pandas as pd

REQUIRED_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "amount"
]


def validate_dataset(df, source):
    """Validate required fields and basic data types."""

    missing = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(
            f"{source}: Missing columns {missing}"
        )

    if df["transaction_id"].isna().any():
        raise ValueError(
            f"{source}: Null transaction IDs found"
        )

    if df["amount"].isna().any():
        raise ValueError(
            f"{source}: Null amounts found"
        )

    if not pd.api.types.is_numeric_dtype(df["amount"]):
        raise ValueError(
            f"{source}: Amount must be numeric"
        )

    if (df["amount"] < 0).any():
        raise ValueError(
            f"{source}: Negative amounts found"
        )


def reconcile(bank_df, gateway_df):

    validate_dataset(bank_df, "Bank")
    validate_dataset(gateway_df, "Gateway")

    bank = bank_df.copy()
    gateway = gateway_df.copy()

    # Standardize transaction IDs
    bank["transaction_id"] = (
        bank["transaction_id"].astype(str).str.strip()
    )

    gateway["transaction_id"] = (
        gateway["transaction_id"].astype(str).str.strip()
    )

    # Standardize dates and amounts
    for df in [bank, gateway]:
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], errors="raise"
        )
        df["amount"] = df["amount"].round(2)

    exceptions = []

    # Identify duplicate IDs
    bank_counts = bank["transaction_id"].value_counts()
    gateway_counts = gateway["transaction_id"].value_counts()

    duplicate_bank_ids = set(
        bank_counts[bank_counts > 1].index
    )

    duplicate_gateway_ids = set(
        gateway_counts[gateway_counts > 1].index
    )

    all_duplicate_ids = (
        duplicate_bank_ids | duplicate_gateway_ids
    )

    # Create duplicate exception records
    for transaction_id in sorted(all_duplicate_ids):

        exceptions.append({
            "transaction_id": transaction_id,
            "amount_bank": None,
            "amount_gateway": None,
            "variance": None,
            "status": (
                "DUPLICATE_IN_BOTH"
                if transaction_id in duplicate_bank_ids
                and transaction_id in duplicate_gateway_ids
                else "DUPLICATE_IN_BANK"
                if transaction_id in duplicate_bank_ids
                else "DUPLICATE_IN_GATEWAY"
            ),
            "exception_reason": "Duplicate transaction ID",
            "duplicate_bank_count": int(
                bank_counts.get(transaction_id, 0)
            ),
            "duplicate_gateway_count": int(
                gateway_counts.get(transaction_id, 0)
            )
        })

    # Exclude ambiguous duplicate IDs from matching
    bank_unique = bank[
        ~bank["transaction_id"].isin(all_duplicate_ids)
    ]

    gateway_unique = gateway[
        ~gateway["transaction_id"].isin(all_duplicate_ids)
    ]

    # Match unique transaction IDs
    merged = bank_unique.merge(
        gateway_unique,
        on="transaction_id",
        how="outer",
        suffixes=("_bank", "_gateway"),
        indicator=True,
        validate="one_to_one"
    )

    # Classify each transaction
    def classify(row):

        if row["_merge"] == "left_only":
            return "MISSING_IN_GATEWAY"

        if row["_merge"] == "right_only":
            return "MISSING_IN_BANK"

        amount_match = (
            row["amount_bank"] == row["amount_gateway"]
        )

        date_match = (
            row["transaction_date_bank"]
            == row["transaction_date_gateway"]
        )

        if amount_match and date_match:
            return "MATCHED"

        if not amount_match and not date_match:
            return "AMOUNT_AND_DATE_MISMATCH"

        if not amount_match:
            return "AMOUNT_MISMATCH"

        return "DATE_MISMATCH"

    merged["status"] = merged.apply(classify, axis=1)

    # Calculate financial variance
    merged["variance"] = (
        merged["amount_bank"] - merged["amount_gateway"]
    ).round(2)

    # Generate exception descriptions
    merged["exception_reason"] = merged["status"].map({
        "MATCHED": "No discrepancy",
        "AMOUNT_MISMATCH": "Transaction amounts differ",
        "DATE_MISMATCH": "Transaction dates differ",
        "AMOUNT_AND_DATE_MISMATCH":
            "Transaction amounts and dates differ",
        "MISSING_IN_GATEWAY":
            "Transaction missing from gateway",
        "MISSING_IN_BANK":
            "Transaction missing from bank"
    })

    # Standardize output columns
    merged = merged.rename(columns={
        "transaction_date_bank": "date_bank",
        "transaction_date_gateway": "date_gateway"
    })

    # Build duplicate exception dataframe
    duplicate_df = pd.DataFrame(exceptions)

    # Combine reconciliation results
    results = pd.concat(
        [merged, duplicate_df],
        ignore_index=True,
        sort=False
    )

    return results


def reconcile_with_fuzzy(
    bank_df,
    gateway_df,
    minimum_score=70,
    date_window_days=3
):
    """
    Run exact reconciliation first, then identify fuzzy
    candidates among transactions that remain unmatched.

    Returns:
        results: Existing exact reconciliation results.
        fuzzy_candidates: Potential matches for investigation.
    """

    # 1. Run the existing exact reconciliation engine.
    results = reconcile(bank_df, gateway_df)

    # 2. Identify bank transactions missing from the gateway.
    bank_unmatched_ids = results.loc[
        results["status"] == "MISSING_IN_GATEWAY",
        "transaction_id"
    ].dropna().unique()

    # 3. Identify gateway transactions missing from the bank.
    gateway_unmatched_ids = results.loc[
        results["status"] == "MISSING_IN_BANK",
        "transaction_id"
    ].dropna().unique()

    # 4. Retrieve the original unmatched transactions.
    bank_unmatched = bank_df[
        bank_df["transaction_id"].astype(str).str.strip().isin(
            bank_unmatched_ids
        )
    ].copy()

    gateway_unmatched = gateway_df[
        gateway_df["transaction_id"].astype(str).str.strip().isin(
            gateway_unmatched_ids
        )
    ].copy()

    # 5. Search for possible fuzzy matches.
    fuzzy_candidates = find_fuzzy_candidates(
        bank_unmatched,
        gateway_unmatched,
        minimum_score=minimum_score,
        date_window_days=date_window_days
    )

    return results, fuzzy_candidates


def generate_summary(results):

    summary = results["status"].value_counts()

    print("\nRECONCILIATION SUMMARY")
    print("=" * 40)

    print(f"Total records: {len(results):,}")

    for status, count in summary.items():
        print(f"{status}: {count:,}")

    matched = (results["status"] == "MATCHED").sum()

    match_rate = (
        matched / len(results) * 100
        if len(results) else 0
    )

    print(f"\nMatch rate: {match_rate:.2f}%")

    return summary
