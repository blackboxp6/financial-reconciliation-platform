
import pandas as pd

from reconciliation.validation import validate_dataset


sample_data = pd.DataFrame({
    "transaction_id": [
        "TXN001",
        "TXN002",
        "",
        "TXN004",
        "TXN005"
    ],
    "transaction_date": [
        "2026-10-01",
        "invalid-date",
        "2026-10-03",
        "2026-10-04",
        "2026-10-05"
    ],
    "amount": [
        5000,
        3000,
        2000,
        "ABC",
        1000
    ]
})


valid, rejected, report = validate_dataset(
    sample_data,
    "BANK"
)

print("\nVALID RECORDS")
print(valid)

print("\nQUARANTINED RECORDS")
print(rejected)

print("\nDATA QUALITY REPORT")
print(report)
