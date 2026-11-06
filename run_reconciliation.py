
import pandas as pd
import json

from pathlib import Path

from reconciliation.engine import (
    reconcile_with_fuzzy,
    generate_summary
)

from reconciliation.reporting import (
    generate_financial_report,
    display_financial_report
)

from reconciliation.audit import (
    generate_run_id,
    get_timestamp,
    log_event
)

from reconciliation.validation import validate_dataset


def main():

    # 1. Define project directories
    INPUT_DIR = Path("data/raw")
    OUTPUT_DIR = Path("data/processed")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 2. Generate unique run ID
    run_id = generate_run_id()

    print("=" * 55)
    print("FINANCIAL DATA RECONCILIATION PLATFORM")
    print("=" * 55)

    print(f"Run ID: {run_id}")

    try:

        # 3. Record process start
        log_event(
            run_id,
            "RECONCILIATION_STARTED",
            "SUCCESS",
            "Reconciliation process started"
        )

        # 4. Load datasets
        print("\n[1] Loading transaction datasets...")

        bank_df = pd.read_csv(
            INPUT_DIR / "bank_transactions.csv"
        )

        gateway_df = pd.read_csv(
            INPUT_DIR / "gateway_transactions.csv"
        )

        print(f"Bank records: {len(bank_df):,}")
        print(f"Gateway records: {len(gateway_df):,}")

        log_event(
            run_id,
            "DATASETS_LOADED",
            "SUCCESS",
            f"Bank: {len(bank_df)}, Gateway: {len(gateway_df)}"
        )

        # 5. Validate bank dataset
        print("\n[2] Validating bank dataset...")

        bank_valid, bank_rejected, bank_quality = (
            validate_dataset(bank_df, "BANK")
        )

        # 6. Validate gateway dataset
        print("\n[3] Validating gateway dataset...")

        gateway_valid, gateway_rejected, gateway_quality = (
            validate_dataset(gateway_df, "GATEWAY")
        )

        # 7. Combine data quality reports
        quality_report = {
            "run_id": run_id,
            "validated_at": get_timestamp(),
            "sources": [
                bank_quality,
                gateway_quality
            ],
            "total_input_rows": (
                bank_quality["input_rows"]
                + gateway_quality["input_rows"]
            ),
            "total_valid_rows": (
                bank_quality["valid_rows"]
                + gateway_quality["valid_rows"]
            ),
            "total_quarantined_rows": (
                bank_quality["quarantined_rows"]
                + gateway_quality["quarantined_rows"]
            )
        }

        print("\nDATA QUALITY SUMMARY")
        print("=" * 55)

        print(
            f"Total input rows: "
            f"{quality_report['total_input_rows']:,}"
        )

        print(
            f"Valid rows: "
            f"{quality_report['total_valid_rows']:,}"
        )

        print(
            f"Quarantined rows: "
            f"{quality_report['total_quarantined_rows']:,}"
        )

        # 8. Combine quarantined records
        quarantined_records = pd.concat(
            [
                bank_rejected,
                gateway_rejected
            ],
            ignore_index=True
        )

        # 9. Record validation event
        log_event(
            run_id,
            "DATA_QUALITY_VALIDATED",
            "SUCCESS",
            f"Valid: {quality_report['total_valid_rows']}; "
            f"Quarantined: "
            f"{quality_report['total_quarantined_rows']}"
        )

        # 10. Execute exact and fuzzy reconciliation
        print("\n[4] Executing reconciliation...")

        results, fuzzy_candidates = reconcile_with_fuzzy(
            bank_valid,
            gateway_valid,
            minimum_score=70,
            date_window_days=3
        )

        # 11. Attach execution metadata
        reconciliation_timestamp = get_timestamp()

        results["run_id"] = run_id
        results["reconciled_at"] = reconciliation_timestamp

        # 12. Attach metadata to fuzzy candidates
        if fuzzy_candidates.empty:

            fuzzy_candidates = pd.DataFrame(
                columns=[
                    "transaction_id_bank",
                    "transaction_id_gateway",
                    "amount_bank",
                    "amount_gateway",
                    "date_bank",
                    "date_gateway",
                    "match_score",
                    "date_difference_days",
                    "bank_candidate_rank",
                    "gateway_candidate_rank",
                    "is_mutual_best",
                    "review_status",
                    "run_id",
                    "generated_at"
                ]
            )

        else:

            fuzzy_candidates["run_id"] = run_id

            fuzzy_candidates["generated_at"] = (
                reconciliation_timestamp
            )

        # 13. Display fuzzy matching summary
        print("\nFUZZY MATCHING SUMMARY")
        print("=" * 55)

        print(
            f"Potential candidates: "
            f"{len(fuzzy_candidates):,}"
        )

        if not fuzzy_candidates.empty:

            mutual_best_count = int(
                fuzzy_candidates["is_mutual_best"].sum()
            )

            ambiguous_count = (
                len(fuzzy_candidates) - mutual_best_count
            )

            print(
                f"Mutual best candidates: "
                f"{mutual_best_count:,}"
            )

            print(
                f"Ambiguous candidates: "
                f"{ambiguous_count:,}"
            )

            print("\nTOP FUZZY CANDIDATES")

            print(
                fuzzy_candidates[
                    [
                        "transaction_id_bank",
                        "transaction_id_gateway",
                        "match_score",
                        "review_status"
                    ]
                ].head(10).to_string(index=False)
            )

        else:

            print("No fuzzy candidates found.")

        # 14. Record fuzzy matching event
        log_event(
            run_id,
            "FUZZY_MATCHING_COMPLETED",
            "SUCCESS",
            f"Generated {len(fuzzy_candidates)} "
            f"potential candidates"
        )

        # 15. Generate reconciliation summary
        print("\n[5] Generating reconciliation summary...")

        generate_summary(results)

        # 16. Financial impact analysis
        print("\n[6] Performing financial impact analysis...")

        financial_report = generate_financial_report(
            results
        )

        display_financial_report(
            financial_report
        )

        financial_report["run_id"] = run_id
        financial_report["reconciled_at"] = (
            reconciliation_timestamp
        )

        # 17. Generate exception dataset
        exceptions = results[
            results["status"] != "MATCHED"
        ].copy()

        # 18. Save reconciliation reports
        print("\n[7] Saving reports...")

        results.to_csv(
            OUTPUT_DIR / "reconciliation_results.csv",
            index=False
        )

        exceptions.to_csv(
            OUTPUT_DIR / "reconciliation_exceptions.csv",
            index=False
        )

        # 19. Save fuzzy matching candidates
        fuzzy_candidates.to_csv(
            OUTPUT_DIR / "fuzzy_match_candidates.csv",
            index=False
        )

        # 20. Save quarantined records
        quarantined_records.to_csv(
            OUTPUT_DIR / "quarantined_records.csv",
            index=False
        )

        # 21. Save financial impact report
        with open(
            OUTPUT_DIR / "financial_impact_report.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                financial_report,
                file,
                indent=4,
                default=str
            )

        # 22. Save data quality report
        with open(
            OUTPUT_DIR / "data_quality_report.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                quality_report,
                file,
                indent=4,
                default=str
            )

        # 23. Record successful completion
        log_event(
            run_id,
            "RECONCILIATION_COMPLETED",
            "SUCCESS",
            f"Processed {len(results)} reconciliation records; "
            f"found {len(exceptions)} exceptions; "
            f"generated {len(fuzzy_candidates)} fuzzy candidates"
        )

        # 24. Final execution summary
        print("\n" + "=" * 55)
        print("RECONCILIATION COMPLETED SUCCESSFULLY")
        print("=" * 55)

        print(f"Run ID: {run_id}")

        print(
            f"Reconciliation records: {len(results):,}"
        )

        print(
            f"Matched transactions: "
            f"{(results['status'] == 'MATCHED').sum():,}"
        )

        print(
            f"Reconciliation exceptions: {len(exceptions):,}"
        )

        print(
            f"Fuzzy candidates: {len(fuzzy_candidates):,}"
        )

        print(
            f"Quarantined records: "
            f"{len(quarantined_records):,}"
        )

        print("\nGenerated files:")

        for file_path in sorted(OUTPUT_DIR.iterdir()):

            if file_path.is_file():
                print(f" - {file_path}")

        print("\nAll reports saved successfully.")

    except Exception as error:

        # Record failed execution
        log_event(
            run_id,
            "RECONCILIATION_FAILED",
            "FAILED",
            str(error)
        )

        print(f"\nRECONCILIATION FAILED: {error}")

        raise


if __name__ == "__main__":
    main()
