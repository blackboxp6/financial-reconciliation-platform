
import json
import pandas as pd

from pathlib import Path
from datetime import datetime, timezone


# ==================================================
# PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_FILE = (
    PROJECT_ROOT / "data/processed/reconciliation_results_with_fuzzy.csv"
)

DECISIONS_FILE = (
    PROJECT_ROOT / "data/processed/production_fuzzy_review_decisions.csv"
)

CANDIDATES_FILE = (
    PROJECT_ROOT / "data/processed/fuzzy_match_candidates.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data/processed"

JSON_REPORT = OUTPUT_DIR / "management_report.json"

PRIORITY_REPORT = (
    OUTPUT_DIR / "management_exception_priorities.csv"
)

HIGH_VALUE_THRESHOLD = 50000


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def safe_sum(series):
    """Safely calculate a numeric total."""

    return round(
        pd.to_numeric(series, errors="coerce")
        .fillna(0)
        .sum(),
        2
    )


def count_status(df, status):
    """Count records belonging to a specific status."""

    return int((df["status"] == status).sum())


# ==================================================
# FINANCIAL EXCEPTION ANALYSIS
# ==================================================

def build_exception_report(results):

    exceptions = results[
        ~results["status"].isin([
            "MATCHED",
            "FUZZY_MATCH_APPROVED"
        ])
    ].copy()

    exceptions["amount_bank"] = pd.to_numeric(
        exceptions["amount_bank"],
        errors="coerce"
    )

    exceptions["amount_gateway"] = pd.to_numeric(
        exceptions["amount_gateway"],
        errors="coerce"
    )

    exceptions["variance"] = pd.to_numeric(
        exceptions["variance"],
        errors="coerce"
    )

    def calculate_investigation_value(row):

        status = row["status"]

        if status in [
            "AMOUNT_MISMATCH",
            "DATE_MISMATCH",
            "AMOUNT_AND_DATE_MISMATCH"
        ]:
            return abs(row["variance"]) if pd.notna(
                row["variance"]
            ) else 0

        if status == "MISSING_IN_GATEWAY":
            return (
                row["amount_bank"]
                if pd.notna(row["amount_bank"])
                else 0
            )

        if status == "MISSING_IN_BANK":
            return (
                row["amount_gateway"]
                if pd.notna(row["amount_gateway"])
                else 0
            )

        # Duplicate records need investigation.
        # Their monetary exposure is not quantified here.
        return 0

    exceptions["investigation_value"] = exceptions.apply(
        calculate_investigation_value,
        axis=1
    )

    exceptions["priority"] = exceptions[
        "investigation_value"
    ].apply(
        lambda value:
            "HIGH"
            if value >= HIGH_VALUE_THRESHOLD
            else "NORMAL"
    )

    priority_columns = [
        "transaction_id",
        "transaction_id_bank",
        "transaction_id_gateway",
        "status",
        "exception_reason",
        "amount_bank",
        "amount_gateway",
        "variance",
        "investigation_value",
        "priority"
    ]

    # Retain only columns that exist.
    priority_columns = [
        column
        for column in priority_columns
        if column in exceptions.columns
    ]

    priority_report = exceptions[
        priority_columns
    ].sort_values(
        "investigation_value",
        ascending=False
    )

    return exceptions, priority_report


# ==================================================
# MANAGEMENT RECOMMENDATIONS
# ==================================================

def generate_recommendations(report):

    recommendations = []

    if report["missing_in_gateway"] > 0:

        recommendations.append(
            "Investigate transactions recorded by the bank "
            "but absent from the gateway. Coordinate with "
            "the payment gateway operations team."
        )

    if report["missing_in_bank"] > 0:

        recommendations.append(
            "Investigate transactions recorded by the gateway "
            "but absent from the bank. Verify settlement and "
            "posting records."
        )

    if report["amount_mismatch_count"] > 0:

        recommendations.append(
            "Prioritize amount discrepancies based on "
            "financial exposure and transaction value."
        )

    if report["duplicate_count"] > 0:

        recommendations.append(
            "Investigate duplicate transaction identifiers "
            "before allowing automatic processing."
        )

    if report["fuzzy_review_rejection_rate"] > 0:

        recommendations.append(
            "Analyze rejected fuzzy candidates to identify "
            "features that could improve matching accuracy."
        )

    if not recommendations:

        recommendations.append(
            "No outstanding exceptions detected. "
            "Continue routine reconciliation monitoring."
        )

    return recommendations


# ==================================================
# MAIN MANAGEMENT REPORT
# ==================================================

def main():

    print("=" * 65)
    print("FINANCIAL RECONCILIATION MANAGEMENT REPORT")
    print("=" * 65)

    # 1. Load data
    for file_path in [
        RESULTS_FILE,
        DECISIONS_FILE,
        CANDIDATES_FILE
    ]:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

    results = pd.read_csv(RESULTS_FILE)
    decisions = pd.read_csv(DECISIONS_FILE)
    candidates = pd.read_csv(CANDIDATES_FILE)

    # 2. Count reconciliation outcomes
    total_records = len(results)

    exact_matches = count_status(
        results,
        "MATCHED"
    )

    fuzzy_matches = count_status(
        results,
        "FUZZY_MATCH_APPROVED"
    )

    missing_gateway = count_status(
        results,
        "MISSING_IN_GATEWAY"
    )

    missing_bank = count_status(
        results,
        "MISSING_IN_BANK"
    )

    amount_mismatches = count_status(
        results,
        "AMOUNT_MISMATCH"
    )

    date_mismatches = count_status(
        results,
        "DATE_MISMATCH"
    )

    combined_mismatches = count_status(
        results,
        "AMOUNT_AND_DATE_MISMATCH"
    )

    duplicate_count = int(
        results["status"].astype(str).str.startswith(
            "DUPLICATE"
        ).sum()
    )

    matched_total = exact_matches + fuzzy_matches

    output_row_match_rate = (
        matched_total / total_records * 100
        if total_records else 0
    )

    # 3. Calculate financial exposure
    exceptions, priority_report = build_exception_report(
        results
    )

    amount_mismatch_exposure = safe_sum(
        exceptions.loc[
            exceptions["status"].isin([
                "AMOUNT_MISMATCH",
                "AMOUNT_AND_DATE_MISMATCH"
            ]),
            "investigation_value"
        ]
    )

    missing_gateway_value = safe_sum(
        exceptions.loc[
            exceptions["status"] == "MISSING_IN_GATEWAY",
            "investigation_value"
        ]
    )

    missing_bank_value = safe_sum(
        exceptions.loc[
            exceptions["status"] == "MISSING_IN_BANK",
            "investigation_value"
        ]
    )

    gross_investigation_amount = (
        amount_mismatch_exposure
        + missing_gateway_value
        + missing_bank_value
    )

    # 4. Evaluate analyst decisions
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

    approved_count = int(
        (latest_decisions["decision"] == "APPROVED").sum()
    )

    rejected_count = int(
        (latest_decisions["decision"] == "REJECTED").sum()
    )

    deferred_count = int(
        (latest_decisions["decision"] == "DEFERRED").sum()
    )

    reviewed_count = len(latest_decisions)

    rejection_rate = (
        rejected_count / reviewed_count * 100
        if reviewed_count else 0
    )

    acceptance_rate = (
        approved_count / reviewed_count * 100
        if reviewed_count else 0
    )

    # 5. Construct management report
    report = {

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "reconciliation": {

            "total_output_records": total_records,

            "exact_matches": exact_matches,

            "approved_fuzzy_matches": fuzzy_matches,

            "total_matched_pairs": matched_total,

            "output_row_match_rate_percent": round(
                output_row_match_rate,
                2
            )
        },

        "outstanding_exceptions": {

            "missing_in_gateway": missing_gateway,

            "missing_in_bank": missing_bank,

            "amount_mismatches": amount_mismatches,

            "date_mismatches": date_mismatches,

            "amount_and_date_mismatches": combined_mismatches,

            "duplicates": duplicate_count,

            "total_open_exceptions": len(exceptions)
        },

        "financial_exposure_php": {

            "amount_mismatch_exposure": amount_mismatch_exposure,

            "missing_gateway_value": missing_gateway_value,

            "missing_bank_value": missing_bank_value,

            "gross_investigation_amount": round(
                gross_investigation_amount,
                2
            ),

            "note": (
                "Indicative amounts requiring investigation, "
                "not confirmed financial losses. Components may "
                "overlap economically. Duplicate exposure is "
                "not quantified."
            )
        },

        "analyst_review": {

            "total_candidates_generated": len(candidates),

            "total_candidates_reviewed": reviewed_count,

            "approved": approved_count,

            "rejected": rejected_count,

            "deferred": deferred_count,

            "acceptance_rate_percent": round(
                acceptance_rate,
                2
            ),

            "rejection_rate_percent": round(
                rejection_rate,
                2
            )
        }
    }

    # 6. Generate management recommendations
    report["management_recommendations"] = (
        generate_recommendations({
            "missing_in_gateway": missing_gateway,
            "missing_in_bank": missing_bank,
            "amount_mismatch_count": (
                amount_mismatches + combined_mismatches
            ),
            "duplicate_count": duplicate_count,
            "fuzzy_review_rejection_rate": rejection_rate
        })
    )

    # 7. Save JSON report
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        JSON_REPORT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    # 8. Save prioritized exception list
    priority_report.to_csv(
        PRIORITY_REPORT,
        index=False
    )

    # 9. Display management summary
    print("\nRECONCILIATION PERFORMANCE")
    print("-" * 50)

    print(f"Total output records: {total_records:,}")
    print(f"Exact matches: {exact_matches:,}")
    print(f"Approved fuzzy matches: {fuzzy_matches:,}")
    print(f"Total matched pairs: {matched_total:,}")

    print(
        f"Output-row match rate: "
        f"{output_row_match_rate:.2f}%"
    )

    print("\nOUTSTANDING EXCEPTIONS")
    print("-" * 50)

    print(f"Missing in gateway: {missing_gateway:,}")
    print(f"Missing in bank: {missing_bank:,}")
    print(f"Amount mismatches: {amount_mismatches:,}")
    print(f"Date mismatches: {date_mismatches:,}")
    print(f"Combined mismatches: {combined_mismatches:,}")
    print(f"Duplicates: {duplicate_count:,}")

    print("\nFINANCIAL INVESTIGATION EXPOSURE")
    print("-" * 50)

    print(
        f"Amount mismatch exposure: "
        f"PHP {amount_mismatch_exposure:,.2f}"
    )

    print(
        f"Missing gateway value: "
        f"PHP {missing_gateway_value:,.2f}"
    )

    print(
        f"Missing bank value: "
        f"PHP {missing_bank_value:,.2f}"
    )

    print(
        f"Gross investigation amount: "
        f"PHP {gross_investigation_amount:,.2f}"
    )

    print("\nANALYST REVIEW PERFORMANCE")
    print("-" * 50)

    print(f"Candidates generated: {len(candidates):,}")
    print(f"Candidates reviewed: {reviewed_count:,}")
    print(f"Approved: {approved_count:,}")
    print(f"Rejected: {rejected_count:,}")
    print(f"Deferred: {deferred_count:,}")
    print(f"Acceptance rate: {acceptance_rate:.2f}%")

    print("\nMANAGEMENT RECOMMENDATIONS")
    print("-" * 50)

    for number, recommendation in enumerate(
        report["management_recommendations"],
        start=1
    ):

        print(f"{number}. {recommendation}")

    print("\n" + "=" * 65)
    print("MANAGEMENT REPORT GENERATED")
    print("=" * 65)

    print(f"JSON report: {JSON_REPORT}")
    print(f"Priority report: {PRIORITY_REPORT}")


if __name__ == "__main__":
    main()
