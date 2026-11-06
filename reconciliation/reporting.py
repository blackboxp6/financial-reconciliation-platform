
import pandas as pd


def generate_financial_report(results):

    # Count transaction statuses
    status_counts = results["status"].value_counts()

    total_records = len(results)

    matched = int(
        status_counts.get("MATCHED", 0)
    )

    exceptions = total_records - matched

    match_rate = (
        matched / total_records * 100
        if total_records > 0 else 0
    )

    # Calculate amount mismatch exposure
    amount_mismatch = results[
        results["status"].isin([
            "AMOUNT_MISMATCH",
            "AMOUNT_AND_DATE_MISMATCH"
        ])
    ]

    amount_variance = (
        amount_mismatch["variance"]
        .abs()
        .sum()
    )

    # Missing from gateway:
    # Money recorded by bank but absent in gateway
    missing_gateway = results[
        results["status"] == "MISSING_IN_GATEWAY"
    ]

    missing_gateway_value = (
        missing_gateway["amount_bank"].sum()
    )

    # Missing from bank:
    # Money recorded by gateway but absent in bank
    missing_bank = results[
        results["status"] == "MISSING_IN_BANK"
    ]

    missing_bank_value = (
        missing_bank["amount_gateway"].sum()
    )

    # Quantified exception amount
    quantified_exposure = (
        amount_variance
        + missing_gateway_value
        + missing_bank_value
    )

    # Summary
    report = {
        "total_records": total_records,
        "matched_records": matched,
        "exception_records": exceptions,
        "match_rate_percent": round(match_rate, 2),
        "amount_mismatch_count": len(amount_mismatch),
        "amount_variance": round(amount_variance, 2),
        "missing_gateway_count": len(missing_gateway),
        "missing_gateway_value": round(
            missing_gateway_value, 2
        ),
        "missing_bank_count": len(missing_bank),
        "missing_bank_value": round(
            missing_bank_value, 2
        ),
        "quantified_exception_amount": round(
            quantified_exposure, 2
        )
    }

    return report


def display_financial_report(report):

    print("\nFINANCIAL IMPACT REPORT")
    print("=" * 50)

    for key, value in report.items():

        if "value" in key or "amount" in key or "variance" in key:
            print(f"{key}: PHP {value:,.2f}")

        else:
            print(f"{key}: {value:,}" if isinstance(value, int) else f"{key}: {value}")
