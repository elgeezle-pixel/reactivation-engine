import csv
import os
from datetime import date, datetime

LOG_COLUMNS = ["number", "name", "date", "source"]


def log_path(folder):
    return os.path.join(folder, "contact_log.csv")


def load_contacted(folder):
    """Return {whatsapp number: most recent contact date}.
    Stops the run if a log row can't be read, because a silently skipped
    row could mean messaging someone twice."""
    path = log_path(folder)
    latest = {}
    if not os.path.exists(path):
        return latest
    with open(path, encoding="utf-8") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            number = (row.get("number") or "").strip()
            try:
                when = datetime.strptime((row.get("date") or "").strip(), "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"{path} line {line_number} has an unreadable date. "
                                 "Fix it before running, or patients may be messaged twice.")
            if not number:
                raise ValueError(f"{path} line {line_number} has no number.")
            if number not in latest or when > latest[number]:
                latest[number] = when
    return latest


def record_contacts(folder, entries, source, when=None):
    """Append one log row per entry. Each entry needs 'number' and 'name'."""
    when = when or date.today()
    path = log_path(folder)
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if new_file:
            writer.writeheader()
        for entry in entries:
            writer.writerow({"number": entry["number"], "name": entry["name"],
                             "date": when.isoformat(), "source": source})
    return len(entries)