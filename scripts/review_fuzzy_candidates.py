
import pandas as pd
import uuid
import sys

from pathlib import Path
from datetime import datetime, timezone

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reconciliation.audit import log_event


INPUT_FILE = PROJECT_ROOT / "data/processed/fuzzy_match_candidates.csv"

OUTPUT_FILE = PROJECT_ROOT / "data/processed/production_fuzzy_review_decisions.csv"

# --------------------------------------------------
# MAIN REVIEW FUNCTION
# --------------------------------------------------

def main():

    print("=" * 60)
    print("FUZZY MATCH HUMAN REVIEW")
    print("=" * 60)

    # 1. Check candidate file
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {INPUT_FILE}"
        )

    candidates = pd.read_csv(INPUT_FILE)

    if candidates.empty:
        print("No candidates available for review.")
        return

    # 2. Identify reviewer
    reviewer = input(
        "Enter reviewer name or ID: "
    ).strip()

    if not reviewer:
        raise ValueError("Reviewer is required.")

    # 3. Generate review session ID
    review_batch_id = str(uuid.uuid4())

    decisions = []

    print(f"\nReview batch ID: {review_batch_id}")
    print(f"Candidates to review: {len(candidates)}")
    print("A = Approve | R = Reject | D = Defer")

    # --------------------------------------------------
    # 4. REVIEW EACH CANDIDATE
    # --------------------------------------------------

    for index, row in candidates.iterrows():

        print("\n" + "-" * 60)
        print(f"Candidate {index + 1} of {len(candidates)}")

        print(
            f"Bank ID: {row['transaction_id_bank']}"
        )

        print(
            f"Gateway ID: {row['transaction_id_gateway']}"
        )

        print(f"Match score: {row['match_score']}")

        if "amount_score" in candidates.columns:
            print(f"Amount score: {row['amount_score']}")

        if "date_score" in candidates.columns:
            print(f"Date score: {row['date_score']}")

        if "type_match" in candidates.columns:
            print(
                f"Transaction type agrees: "
                f"{row['type_match']}"
            )

        if "channel_match" in candidates.columns:
            print(
                f"Channel agrees: "
                f"{row['channel_match']}"
            )

        if "review_reason" in candidates.columns:
            print(f"Review reason: {row['review_reason']}")

        # 5. Capture reviewer decision
        choice = input(
            "\nDecision (A/R/D): "
        ).strip().upper()

        decision_map = {
            "A": "APPROVED",
            "R": "REJECTED",
            "D": "DEFERRED"
        }

        if choice not in decision_map:
            print("Invalid choice. Candidate deferred.")
            decision = "DEFERRED"
        else:
            decision = decision_map[choice]

        reason = input(
            "Reviewer comments (optional): "
        ).strip()

        reviewed_at = datetime.now(
            timezone.utc
        ).isoformat()

        # 6. Store decision in memory
        decisions.append({
            "review_batch_id": review_batch_id,
            "reviewed_at": reviewed_at,
            "reviewer": reviewer,
            "transaction_id_bank":
                row["transaction_id_bank"],
            "transaction_id_gateway":
                row["transaction_id_gateway"],
            "match_score": row["match_score"],
            "decision": decision,
            "reviewer_comments": reason
        })

        print(f"Recorded decision: {decision}")

    # --------------------------------------------------
    # 7. SAVE REVIEW DECISIONS
    # --------------------------------------------------

    decision_df = pd.DataFrame(decisions)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = OUTPUT_FILE.exists()

    decision_df.to_csv(
        OUTPUT_FILE,
        mode="a",
        header=not file_exists,
        index=False
    )

    print("\nReview decisions saved successfully.")

    # --------------------------------------------------
    # 8. WRITE EVENTS TO AUDIT LOG
    # --------------------------------------------------

    print("\nRecording decisions in audit log...")

    for _, decision_row in decision_df.iterrows():

        details = (
            f"Reviewer: {decision_row['reviewer']} | "
            f"Bank ID: {decision_row['transaction_id_bank']} | "
            f"Gateway ID: {decision_row['transaction_id_gateway']} | "
            f"Score: {decision_row['match_score']} | "
            f"Comments: {decision_row['reviewer_comments']}"
        )

        log_event(
            run_id=review_batch_id,
            event_type="FUZZY_MATCH_REVIEW",
            status=decision_row["decision"],
            details=details
        )

    print("Audit log updated successfully.")

    # --------------------------------------------------
    # 9. REVIEW SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("REVIEW SESSION COMPLETED")
    print("=" * 60)

    print(f"Reviewer: {reviewer}")

    print(
        f"Approved: "
        f"{(decision_df['decision'] == 'APPROVED').sum()}"
    )

    print(
        f"Rejected: "
        f"{(decision_df['decision'] == 'REJECTED').sum()}"
    )

    print(
        f"Deferred: "
        f"{(decision_df['decision'] == 'DEFERRED').sum()}"
    )

    print(f"\nReview decisions: {OUTPUT_FILE}")

    print(
        "Audit log: "
        "data/processed/audit_log.csv"
    )


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
