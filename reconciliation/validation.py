
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "amount"
]


def validate_dataset(df, source):

    """
    Validate a financial transaction dataset.

    Returns:
        clean_df: Valid records ready for reconciliation.
        rejected_df: Invalid records requiring investigation.
        quality_report: Summary of data quality checks.
    """

    # 1. Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{source} dataset is missing columns: "
            f"{missing_columns}"
        )

    # Preserve original records for quarantine
    original_df = df.copy()

    clean_df = df.copy()

    # 2. Normalize transaction IDs
    clean_df["transaction_id"] = (
        clean_df["transaction_id"]
        .astype("string")
        .str.strip()
    )

    missing_id = (
        clean_df["transaction_id"].isna()
        | clean_df["transaction_id"].eq("")
    )

    # 3. Validate transaction dates
    clean_df["transaction_date"] = pd.to_datetime(
        clean_df["transaction_date"],
        errors="coerce"
    )

    invalid_date = clean_df["transaction_date"].isna()

    # 4. Validate transaction amounts
    clean_df["amount"] = pd.to_numeric(
        clean_df["amount"],
        errors="coerce"
    )

    invalid_amount = clean_df["amount"].isna()

    negative_amount = clean_df["amount"].lt(0).fillna(False)

    # 5. Identify invalid rows
    invalid_rows = (
        missing_id
        | invalid_date
        | invalid_amount
        | negative_amount
    )

    # 6. Create quarantine dataset
    rejected_df = original_df.loc[invalid_rows].copy()

    rejected_df["source"] = source

    rejected_df["issue_reason"] = [
        ", ".join(reasons)
        for reasons in zip(
            [
                [
                    issue
                    for issue, condition in [
                        ("MISSING_TRANSACTION_ID", missing_id.iloc[i]),
                        ("INVALID_TRANSACTION_DATE", invalid_date.iloc[i]),
                        ("INVALID_AMOUNT", invalid_amount.iloc[i]),
                        ("NEGATIVE_AMOUNT", negative_amount.iloc[i])
                    ]
                    if condition
                ]
                for i in range(len(clean_df))
            ],
            []
        )
    ] if False else ""

    # Build issue descriptions for each rejected row
    rejected_indices = rejected_df.index

    issue_reasons = []

    for i in rejected_indices:

        reasons = []

        if missing_id.loc[i]:
            reasons.append("MISSING_TRANSACTION_ID")

        if invalid_date.loc[i]:
            reasons.append("INVALID_TRANSACTION_DATE")

        if invalid_amount.loc[i]:
            reasons.append("INVALID_AMOUNT")

        if negative_amount.loc[i]:
            reasons.append("NEGATIVE_AMOUNT")

        issue_reasons.append(", ".join(reasons))

    rejected_df["issue_reason"] = issue_reasons

    # 7. Keep valid records
    valid_df = clean_df.loc[~invalid_rows].copy()

    # 8. Detect duplicates among valid records
    duplicate_mask = valid_df["transaction_id"].duplicated(
        keep=False
    )

    duplicate_ids = (
        valid_df.loc[duplicate_mask, "transaction_id"]
        .nunique()
    )

    duplicate_rows = int(duplicate_mask.sum())

    # 9. Generate data quality report
    quality_report = {
        "source": source,
        "input_rows": len(df),
        "valid_rows": len(valid_df),
        "quarantined_rows": len(rejected_df),
        "missing_transaction_ids": int(missing_id.sum()),
        "invalid_dates": int(invalid_date.sum()),
        "invalid_amounts": int(invalid_amount.sum()),
        "negative_amounts": int(negative_amount.sum()),
        "duplicate_transaction_ids": int(duplicate_ids),
        "duplicate_rows": duplicate_rows
    }

    return valid_df, rejected_df, quality_report
