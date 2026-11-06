
import pandas as pd
from difflib import SequenceMatcher


def text_similarity(value_a, value_b):
    """Return text similarity as a score from 0 to 100."""

    if pd.isna(value_a) or pd.isna(value_b):
        return 0.0

    value_a = str(value_a).strip().lower()
    value_b = str(value_b).strip().lower()

    if not value_a or not value_b:
        return 0.0

    return SequenceMatcher(
        None,
        value_a,
        value_b
    ).ratio() * 100


def amount_similarity(amount_a, amount_b):
    """Compare amounts while allowing small differences."""

    amount_a = float(amount_a)
    amount_b = float(amount_b)

    denominator = max(abs(amount_a), abs(amount_b), 1)

    relative_difference = (
        abs(amount_a - amount_b) / denominator
    )

    # A difference of 5% or more receives zero similarity.
    score = max(
        0,
        100 * (1 - relative_difference / 0.05)
    )

    return score


def date_similarity(date_a, date_b):
    """Score dates based on the number of days between them."""

    date_a = pd.to_datetime(date_a, errors="coerce")
    date_b = pd.to_datetime(date_b, errors="coerce")

    if pd.isna(date_a) or pd.isna(date_b):
        return 0.0

    difference = abs((date_a - date_b).days)

    # Dates more than 3 days apart receive zero similarity.
    return max(0, 100 - (difference * 33.33))



def calculate_match_details(bank_row, gateway_row):
    """Calculate an explainable similarity score."""

    amount_score = amount_similarity(
        bank_row["amount"],
        gateway_row["amount"]
    )

    date_score = date_similarity(
        bank_row["transaction_date"],
        gateway_row["transaction_date"]
    )

    id_score = text_similarity(
        bank_row["transaction_id"],
        gateway_row["transaction_id"]
    )

    type_match = None
    if (
        "transaction_type" in bank_row.index
        and "transaction_type" in gateway_row.index
    ):
        type_match = (
            bank_row["transaction_type"]
            == gateway_row["transaction_type"]
        )

    channel_match = None
    if (
        "channel" in bank_row.index
        and "channel" in gateway_row.index
    ):
        channel_match = (
            bank_row["channel"]
            == gateway_row["channel"]
        )

    # Neutral contribution if an optional field is unavailable.
    type_score = (
        100.0 if type_match else 0.0
    ) if type_match is not None else 50.0

    channel_score = (
        100.0 if channel_match else 0.0
    ) if channel_match is not None else 50.0

    total_score = (
        amount_score * 0.35
        + date_score * 0.30
        + type_score * 0.15
        + channel_score * 0.10
        + id_score * 0.10
    )

    return {
        "match_score": round(total_score, 2),
        "amount_score": round(amount_score, 2),
        "date_score": round(date_score, 2),
        "id_score": round(id_score, 2),
        "type_match": type_match,
        "channel_match": channel_match
    }


def calculate_match_score(bank_row, gateway_row):
    """Return only the overall similarity score."""

    return calculate_match_details(
        bank_row,
        gateway_row
    )["match_score"]


def find_fuzzy_candidates(
    bank_unmatched,
    gateway_unmatched,
    minimum_score=70,
    date_window_days=3
):
    """Generate explainable fuzzy candidates for human review."""

    candidates = []

    bank = bank_unmatched.reset_index(drop=True)
    gateway = gateway_unmatched.reset_index(drop=True)

    for _, bank_row in bank.iterrows():

        for _, gateway_row in gateway.iterrows():

            bank_date = pd.to_datetime(
                bank_row["transaction_date"],
                errors="coerce"
            )

            gateway_date = pd.to_datetime(
                gateway_row["transaction_date"],
                errors="coerce"
            )

            if pd.isna(bank_date) or pd.isna(gateway_date):
                continue

            date_difference = abs(
                (bank_date - gateway_date).days
            )

            if date_difference > date_window_days:
                continue

            details = calculate_match_details(
                bank_row,
                gateway_row
            )

            if details["match_score"] < minimum_score:
                continue

            candidates.append({
                "transaction_id_bank":
                    bank_row["transaction_id"],
                "transaction_id_gateway":
                    gateway_row["transaction_id"],
                "amount_bank": bank_row["amount"],
                "amount_gateway": gateway_row["amount"],
                "date_bank": bank_date,
                "date_gateway": gateway_date,
                "date_difference_days": date_difference,
                **details
            })

    candidate_df = pd.DataFrame(candidates)

    if candidate_df.empty:
        return candidate_df

    candidate_df["bank_candidate_rank"] = (
        candidate_df.groupby("transaction_id_bank")[
            "match_score"
        ].rank(method="dense", ascending=False)
    )

    candidate_df["gateway_candidate_rank"] = (
        candidate_df.groupby("transaction_id_gateway")[
            "match_score"
        ].rank(method="dense", ascending=False)
    )

    candidate_df["is_mutual_best"] = (
        (candidate_df["bank_candidate_rank"] == 1)
        & (candidate_df["gateway_candidate_rank"] == 1)
    )

    def assign_review(row):

        reasons = []

        if not row["is_mutual_best"]:
            reasons.append("NOT_MUTUAL_BEST")

        if row["type_match"] is False:
            reasons.append("TRANSACTION_TYPE_MISMATCH")

        if row["channel_match"] is False:
            reasons.append("CHANNEL_MISMATCH")

        if row["amount_score"] < 80:
            reasons.append("LOW_AMOUNT_SIMILARITY")

        if row["date_difference_days"] > 1:
            reasons.append("DATE_DIFFERENCE_OVER_ONE_DAY")

        # High priority means suitable for review,
        # NOT automatically confirmed.
        if not reasons:
            return pd.Series([
                "REVIEW_HIGH_PRIORITY",
                "No major inconsistencies detected"
            ])

        return pd.Series([
            "REVIEW_REQUIRED",
            "; ".join(reasons)
        ])

    candidate_df[
        ["review_status", "review_reason"]
    ] = candidate_df.apply(
        assign_review,
        axis=1
    )

    return candidate_df.sort_values(
        by="match_score",
        ascending=False
    ).reset_index(drop=True)

