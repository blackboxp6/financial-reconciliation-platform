import csv
import uuid
from pathlib import Path
from datetime import datetime, timezone


AUDIT_FILE = Path("data/processed/audit_log.csv")


def generate_run_id():
    """Generate a unique ID for each reconciliation run."""
    return str(uuid.uuid4())


def get_timestamp():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def log_event(run_id, event_type, status, details):
    """Append an audit event to the audit log."""

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    file_exists = AUDIT_FILE.exists()

    with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "event_id",
                "run_id",
                "timestamp",
                "event_type",
                "status",
                "details"
            ]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "event_id": str(uuid.uuid4()),
            "run_id": run_id,
            "timestamp": get_timestamp(),
            "event_type": event_type,
            "status": status,
            "details": details
        })