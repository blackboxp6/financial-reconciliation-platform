
import sys
from pathlib import Path

import pandas as pd

# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reconciliation.fuzzy_matching import find_fuzzy_candidates


OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "fuzzy_matching_evaluation.csv"


# ============================================================
# 2. CREATE CONTROLLED TEST DATA
# ============================================================

def create_test_data():

    bank_data = [
        {
            "transaction_id": "BANK001",
            "transaction_date": "2026-10-01",
            "amount": 5000.00,
            "transaction_type": "PAYMENT",
            "channel": "ONLINE"
        },
        {
            "transaction_id": "BANK002",
            "transaction_date": "2026-10-10",
            "amount": 7500.00,
            "transaction_type": "TRANSFER",
            "channel": "MOBILE"
        },
        {
            "transaction_id": "BANK003",
            "transaction_date": "2026-10-20",
            "amount": 12000.00,
            "transaction_type": "DEPOSIT",
            "channel": "BRANCH"
        },
        {
            "transaction_id": "BANK004",
            "transaction_date": "2026-10-30",
            "amount": 2500.00,
            "transaction_type": "PAYMENT",
            "channel": "MOBILE"
        }
    ]

    gateway_data = [
        {
            "transaction_id": "GATEWAY901",
            "transaction_date": "2026-10-01",
            "amount": 5000.00,
            "transaction_type": "PAYMENT",
            "channel": "ONLINE"
        },
        {
            "transaction_id": "GATEWAY902",
            "transaction_date": "2026-10-11",
            "amount": 7500.00,
            "transaction_type": "TRANSFER",
            "channel": "MOBILE"
        },
        {
            "transaction_id": "GATEWAY903",
            "transaction_date": "2026-10-20",
            "amount": 12100.00,
            "transaction_type": "DEPOSIT",
            "channel": "BRANCH"
        },
        {
            "transaction_id": "GATEWAY904",
            "transaction_date": "2026-10-30",
            "amount": 2500.00,
            "transaction_type": "PAYMENT",
            "channel": "POS"
        }
    ]

    return (
        pd.DataFrame(bank_data),
        pd.DataFrame(gateway_data)
    )


# ============================================================
# 3. EVALUATE FUZZY MATCHING
# ============================================================

def evaluate_candidates(candidates, expected_pairs):

    if candidates.empty:
        predicted_pairs = set()
    else:
        predicted_pairs = set(
            zip(
                candidates["transaction_id_bank"],
                candidates["transaction_id_gateway"]
            )
        )

    true_positives = len(
        predicted_pairs.intersection(expected_pairs)
    )

    false_positives = len(
        predicted_pairs - expected_pairs
    )

    false_negatives = len(
        expected_pairs - predicted_pairs
    )

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives > 0
        else 0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives > 0
        else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }


# ============================================================
# 4. DISPLAY RESULTS
# ============================================================

def display_candidates(candidates):

    print("\n[4] PREDICTED CANDIDATES")

    if candidates.empty:
        print("No candidates were generated.")
        return

    display_columns = [
        "transaction_id_bank",
        "transaction_id_gateway",
        "match_score",
        "amount_score",
        "date_score",
        "id_score",
        "type_match",
        "channel_match",
        "is_mutual_best",
        "review_status",
        "review_reason"
    ]

    # Display only columns available in the output.
    available_columns = [
        column for column in display_columns
        if column in candidates.columns
    ]

    print(
        candidates[available_columns].to_string(index=False)
    )


def display_metrics(metrics):

    print("\n[5] EVALUATION RESULTS")
    print("-" * 45)

    print(f"True positives:  {metrics['true_positives']}")
    print(f"False positives: {metrics['false_positives']}")
    print(f"False negatives: {metrics['false_negatives']}")

    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall:    {metrics['recall']:.2%}")
    print(f"F1-score:  {metrics['f1_score']:.2%}")


# ============================================================
# 5. MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("FUZZY MATCHING EVALUATION EXPERIMENT")
    print("=" * 60)

    # Generate test data.
    bank_df, gateway_df = create_test_data()

    print("\n[1] TEST DATA")
    print(f"Bank transactions: {len(bank_df)}")
    print(f"Gateway transactions: {len(gateway_df)}")

    # Known genuine transaction pairs.
    expected_pairs = {
        ("BANK001", "GATEWAY901"),
        ("BANK002", "GATEWAY902"),
        ("BANK003", "GATEWAY903")
    }

    print("\n[2] EXPECTED MATCHES")

    for bank_id, gateway_id in sorted(expected_pairs):
        print(f"{bank_id} <-> {gateway_id}")

    print(f"\nKnown genuine matches: {len(expected_pairs)}")
    print("One deliberately misleading pair is included.")

    # Execute fuzzy matching.
    print("\n[3] RUNNING FUZZY MATCHING")

    candidates = find_fuzzy_candidates(
        bank_df,
        gateway_df,
        minimum_score=70,
        date_window_days=3
    )

    print(f"Candidates generated: {len(candidates)}")

    # Display explainable candidate results.
    display_candidates(candidates)

    # Evaluate candidate-generation performance.
    metrics = evaluate_candidates(
        candidates,
        expected_pairs
    )

    display_metrics(metrics)

    # Save experiment results.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n[6] SAVING RESULTS")
    print(f"File: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
