
import sys
import pandas as pd

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reconciliation.audit import log_event


# --------------------------------------------------
# FILE CONFIGURATION
# --------------------------------------------------

RESULTS_FILE = (
    PROJECT_ROOT / "data/processed/reconciliation_results.csv"
)

CANDIDATES_FILE = (
    PROJECT_ROOT / "data/processed/fuzzy_match_candidates.csv"
)

DECISIONS_FILE = (
    PROJECT_ROOT / "data/processed/production_fuzzy_review_decisions.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "data/processed/reconciliation_results_with_fuzzy.csv"
)


# --------------------------------------------------
# APPLY APPROVED MATCHES
# --------------------------------------------------

def main():

    print("=" * 65)
    print("CONTROLLED FUZZY MATCH APPLICATION")
    print("=" * 65)

    # 1. Load required files
    for file_path in [
        RESULTS_FILE,
        CANDIDATES_FILE,
        DECISIONS_FILE
    ]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

    results = pd.read_csv(RESULTS_FILE)
    candidates = pd.read_csv(CANDIDATES_FILE)
    decisions = pd.read_csv(DECISIONS_FILE)

    print(f"Original result rows: {len(results):,}")
    print(f"Fuzzy candidates: {len(candidates):,}")
    print(f"Review decisions: {len(decisions):,}")

    # 2. Check required columns
    required_result_columns = {
        "transaction_id",
        "status",
        "amount_bank",
        "amount_gateway"
    }

    required_candidate_columns = {
        "transaction_id_bank",
        "transaction_id_gateway",
        "match_score"
    }

    required_decision_columns = {
        "transaction_id_bank",
        "transaction_id_gateway",
        "decision",
        "reviewer",
        "review_batch_id"
    }

    if not required_result_columns.issubset(results.columns):
        raise ValueError("Reconciliation results are missing required columns.")

    if not required_candidate_columns.issubset(candidates.columns):
        raise ValueError("Fuzzy candidates are missing required columns.")

    if not required_decision_columns.issubset(decisions.columns):
        raise ValueError("Review decisions are missing required columns.")

    # 3. Keep the latest decision for each transaction pair
    decisions["reviewed_at"] = pd.to_datetime(
        decisions["reviewed_at"],
        errors="coerce",
        utc=True
    )

    decisions = decisions.sort_values(
        "reviewed_at"
    )

    decisions = decisions.drop_duplicates(
        subset=[
            "transaction_id_bank",
            "transaction_id_gateway"
        ],
        keep="last"
    )

    approved = decisions[
        decisions["decision"] == "APPROVED"
    ].copy()

    print(f"\nLatest approved decisions: {len(approved)}")

    # 4. Verify that approved pairs came from candidate generation
    candidate_pairs = set(
        zip(
            candidates["transaction_id_bank"].astype(str),
            candidates["transaction_id_gateway"].astype(str)
        )
    )

    approved_pairs = set(
        zip(
            approved["transaction_id_bank"].astype(str),
            approved["transaction_id_gateway"].astype(str)
        )
    )

    invalid_pairs = approved_pairs - candidate_pairs

    if invalid_pairs:
        raise ValueError(
            f"Some approved pairs are not in the current candidate file: "
            f"{invalid_pairs}"
        )

    # 5. Enforce one-to-one matching
    if approved["transaction_id_bank"].duplicated().any():
        raise ValueError(
            "A bank transaction has multiple approved gateway matches."
        )

    if approved["transaction_id_gateway"].duplicated().any():
        raise ValueError(
            "A gateway transaction has multiple approved bank matches."
        )

    # 6. Build approved fuzzy match records
    matched_rows = []
    indexes_to_remove = []

    for _, decision in approved.iterrows():

        bank_id = str(decision["transaction_id_bank"])
        gateway_id = str(decision["transaction_id_gateway"])

        bank_rows = results[
            (results["transaction_id"].astype(str) == bank_id)
            & (results["status"] == "MISSING_IN_GATEWAY")
        ]

        gateway_rows = results[
            (results["transaction_id"].astype(str) == gateway_id)
            & (results["status"] == "MISSING_IN_BANK")
        ]

        # Require exactly one unmatched row on each side
        if len(bank_rows) != 1 or len(gateway_rows) != 1:
            raise ValueError(
                f"Cannot safely apply pair {bank_id} <-> {gateway_id}. "
                f"Bank unmatched rows: {len(bank_rows)}, "
                f"Gateway unmatched rows: {len(gateway_rows)}"
            )

        bank_row = bank_rows.iloc[0]
        gateway_row = gateway_rows.iloc[0]

        # Start with the bank-side record
        new_row = bank_row.to_dict()

        # Bring gateway-side fields into the same record
        for column in results.columns:

            if column.endswith("_gateway"):
                new_row[column] = gateway_row[column]

        # Preserve both transaction identifiers
        new_row["transaction_id"] = bank_id
        new_row["transaction_id_bank"] = bank_id
        new_row["transaction_id_gateway"] = gateway_id

        # Calculate the difference between the two amounts
        amount_bank = float(bank_row["amount_bank"])
        amount_gateway = float(gateway_row["amount_gateway"])

        new_row["variance"] = round(
            amount_bank - amount_gateway,
            2
        )

        # Record the approved fuzzy match
        new_row["status"] = "FUZZY_MATCH_APPROVED"

        new_row["exception_reason"] = (
            "Fuzzy candidate approved by human reviewer"
        )

        new_row["fuzzy_match_score"] = decision.get(
            "match_score",
            pd.NA
        )

        new_row["reviewer"] = decision["reviewer"]
        new_row["review_batch_id"] = decision["review_batch_id"]

        if "_merge" in new_row:
            new_row["_merge"] = "fuzzy_matched"

        matched_rows.append(new_row)

        # Remove the two original unmatched rows
        indexes_to_remove.extend([
            bank_rows.index[0],
            gateway_rows.index[0]
        ])

    # 7. Build a separate derived result
    updated_results = results.drop(
        index=indexes_to_remove
    ).copy()

    if matched_rows:
        fuzzy_matches_df = pd.DataFrame(matched_rows)

        updated_results = pd.concat(
            [updated_results, fuzzy_matches_df],
            ignore_index=True
        )

    # 8. Save derived results
    updated_results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # 9. Record application events in audit log
    for _, decision in approved.iterrows():

        details = (
            f"Bank ID: {decision['transaction_id_bank']} | "
            f"Gateway ID: {decision['transaction_id_gateway']} | "
            f"Reviewer: {decision['reviewer']}"
        )

        log_event(
            run_id=decision["review_batch_id"],
            event_type="FUZZY_MATCH_APPLIED",
            status="SUCCESS",
            details=details
        )

    # 10. Print summary
    print("\n" + "=" * 65)
    print("APPLICATION SUMMARY")
    print("=" * 65)

    print(f"Approved pairs applied: {len(matched_rows)}")
    print(f"Original rows: {len(results):,}")
    print(f"Updated rows: {len(updated_results):,}")

    print(
        "Fuzzy matches in output: "
        f"{(updated_results['status'] == 'FUZZY_MATCH_APPROVED').sum()}"
    )

    print(
        "Remaining missing in gateway: "
        f"{(updated_results['status'] == 'MISSING_IN_GATEWAY').sum()}"
    )

    print(
        "Remaining missing in bank: "
        f"{(updated_results['status'] == 'MISSING_IN_BANK').sum()}"
    )

    print(f"\nSaved to: {OUTPUT_FILE}")
    print("Audit log updated.")

    print("\nCONTROLLED APPLICATION COMPLETED")


if __name__ == "__main__":
    main()
