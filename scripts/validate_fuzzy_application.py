
import pandas as pd

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORIGINAL_FILE = (
    PROJECT_ROOT / "data/processed/reconciliation_results.csv"
)

UPDATED_FILE = (
    PROJECT_ROOT / "data/processed/reconciliation_results_with_fuzzy.csv"
)

DECISIONS_FILE = (
    PROJECT_ROOT / "data/processed/production_fuzzy_review_decisions.csv"
)


def check(condition, message):

    if condition:
        print(f"[PASS] {message}")
    else:
        print(f"[FAIL] {message}")

    return condition


def main():

    print("=" * 65)
    print("FUZZY APPLICATION QUALITY ASSURANCE")
    print("=" * 65)

    original = pd.read_csv(ORIGINAL_FILE)
    updated = pd.read_csv(UPDATED_FILE)
    decisions = pd.read_csv(DECISIONS_FILE)

    # 1. Identify applied fuzzy matches
    fuzzy_matches = updated[
        updated["status"] == "FUZZY_MATCH_APPROVED"
    ].copy()

    # 2. Get the latest reviewer decision per pair
    decisions["reviewed_at"] = pd.to_datetime(
        decisions["reviewed_at"],
        errors="coerce",
        utc=True
    )

    latest_decisions = (
        decisions.sort_values("reviewed_at")
        .drop_duplicates(
            subset=[
                "transaction_id_bank",
                "transaction_id_gateway"
            ],
            keep="last"
        )
    )

    approved = latest_decisions[
        latest_decisions["decision"] == "APPROVED"
    ]

    applied_pairs = set(
        zip(
            fuzzy_matches["transaction_id_bank"].astype(str),
            fuzzy_matches["transaction_id_gateway"].astype(str)
        )
    )

    approved_pairs = set(
        zip(
            approved["transaction_id_bank"].astype(str),
            approved["transaction_id_gateway"].astype(str)
        )
    )

    results = []

    print("\n[1] RECORD COUNT VALIDATION")

    results.append(check(
        len(original) - len(updated) == len(fuzzy_matches),
        "Each applied pair reduces the result by one row."
    ))

    results.append(check(
        len(fuzzy_matches) == 12,
        "Expected 12 approved fuzzy matches."
    ))

    print("\n[2] APPROVAL VALIDATION")

    results.append(check(
        applied_pairs == approved_pairs,
        "Applied pairs exactly match the latest approved decisions."
    ))

    print("\n[3] ONE-TO-ONE MATCHING VALIDATION")

    results.append(check(
        not fuzzy_matches["transaction_id_bank"].duplicated().any(),
        "No bank transaction is matched more than once."
    ))

    results.append(check(
        not fuzzy_matches["transaction_id_gateway"].duplicated().any(),
        "No gateway transaction is matched more than once."
    ))

    print("\n[4] MISSING TRANSACTION VALIDATION")

    original_missing_gateway = (
        original["status"] == "MISSING_IN_GATEWAY"
    ).sum()

    updated_missing_gateway = (
        updated["status"] == "MISSING_IN_GATEWAY"
    ).sum()

    original_missing_bank = (
        original["status"] == "MISSING_IN_BANK"
    ).sum()

    updated_missing_bank = (
        updated["status"] == "MISSING_IN_BANK"
    ).sum()

    results.append(check(
        original_missing_gateway - updated_missing_gateway
        == len(fuzzy_matches),
        "Missing-in-gateway count decreased correctly."
    ))

    results.append(check(
        original_missing_bank - updated_missing_bank
        == len(fuzzy_matches),
        "Missing-in-bank count decreased correctly."
    ))

    print("\n[5] EXACT MATCH PRESERVATION")

    original_exact = (
        original["status"] == "MATCHED"
    ).sum()

    updated_exact = (
        updated["status"] == "MATCHED"
    ).sum()

    results.append(check(
        original_exact == updated_exact,
        "Original exact matches were preserved."
    ))

    print("\n[6] FUZZY RECORD INTEGRITY")

    results.append(check(
        fuzzy_matches["transaction_id_bank"].notna().all()
        and fuzzy_matches["transaction_id_gateway"].notna().all(),
        "Every fuzzy match contains both transaction IDs."
    ))

    print("\n" + "=" * 65)
    print("QUALITY ASSURANCE SUMMARY")
    print("=" * 65)

    print(f"Original rows: {len(original):,}")
    print(f"Updated rows: {len(updated):,}")
    print(f"Fuzzy matches: {len(fuzzy_matches):,}")

    print(
        f"Remaining missing in gateway: "
        f"{updated_missing_gateway:,}"
    )

    print(
        f"Remaining missing in bank: "
        f"{updated_missing_bank:,}"
    )

    passed = sum(results)
    failed = len(results) - passed

    print(f"\nChecks passed: {passed}")
    print(f"Checks failed: {failed}")

    if failed == 0:
        print("\nALL QUALITY CHECKS PASSED")
    else:
        raise AssertionError(
            "Quality assurance failed. Investigate the failed checks."
        )


if __name__ == "__main__":
    main()
