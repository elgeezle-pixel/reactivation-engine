import csv
import json
import re
import sys
from datetime import date, datetime

REQUIRED_COLUMNS = ["name", "phone", "last_visit"]
REQUIRED_SETTINGS = ["clinic_name", "greeting", "skip_under_months",
                     "due_until_months", "lapsed_until_months"]

# Accepted date formats. Slashes and dashes are read day-first
# (25/10/2026), which is the Nigerian convention.
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# Matches dates like 05/03/2025 or 5-3-2025 (the ambiguous kind)
SHORT_DATE = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")

SEGMENTS = ["recent", "due", "lapsed", "long_gone", "needs_review"]


def load_settings(path):
    with open(path) as f:
        settings = json.load(f)
    missing = [k for k in REQUIRED_SETTINGS if k not in settings]
    if missing:
        raise ValueError(f"{path} is missing setting(s): {', '.join(missing)}")
    if not (settings["skip_under_months"] < settings["due_until_months"]
            < settings["lapsed_until_months"]):
        raise ValueError("Month cut-offs must increase: skip < due < lapsed")
    return settings


def check_date_order(values):
    """Stop the run if any date proves the file is month-first.
    Return a warning if no date proves which order the file uses."""
    proven_day_first = False
    ambiguous = 0
    for text in values:
        match = SHORT_DATE.match(text.strip())
        if not match:
            continue
        first, second = int(match.group(1)), int(match.group(2))
        if second > 12 and first <= 12:
            raise ValueError(
                f"Date '{text}' can only be month-first, but this tool reads "
                "dates day-first. Every date in this file would be misread. "
                "Confirm the clinic's date format before running."
            )
        if first > 12:
            proven_day_first = True
        else:
            ambiguous += 1
    if ambiguous and not proven_day_first:
        return (f"WARNING: {ambiguous} date(s) like 05/03/2025 could be "
                "day-first or month-first, and nothing in this file proves "
                "which. Confirm the format with the clinic before sending.")
    return None


def parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date '{text}'")


def months_between(earlier, later):
    # Whole months only: 25 Jan to 24 Feb is 0 months, to 25 Feb is 1.
    months = (later.year - earlier.year) * 12 + (later.month - earlier.month)
    if later.day < earlier.day:
        months -= 1
    return months


def segment_for(months, settings):
    if months < settings["skip_under_months"]:
        return "recent"
    if months < settings["due_until_months"]:
        return "due"
    if months < settings["lapsed_until_months"]:
        return "lapsed"
    return "long_gone"


def digits_only(phone):
    return "".join(ch for ch in phone if ch.isdigit())


def load_patients(path, settings, today):
    """Read and check the patient file. Every row with a problem goes to
    needs_review with a reason, instead of being guessed at.
    Returns (segments, date_warning)."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        columns = [c.strip() for c in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            raise ValueError(f"{path} is missing column(s): {', '.join(missing)}")
        rows = [{(k or "").strip(): v for k, v in r.items()} for r in reader]

    date_warning = check_date_order([(r.get("last_visit") or "") for r in rows])

    segments = {s: [] for s in SEGMENTS}
    seen_phones = {}

    for row in rows:
        patient = {c: (row.get(c) or "").strip() for c in REQUIRED_COLUMNS}

        problems = []
        if not patient["name"]:
            problems.append("missing name")

        phone_key = digits_only(patient["phone"])
        if not phone_key:
            problems.append("missing phone")
        elif phone_key in seen_phones:
            problems.append(f"duplicate phone (same as {seen_phones[phone_key]})")

        visit = None
        try:
            visit = parse_date(patient["last_visit"])
        except ValueError as error:
            problems.append(str(error))
        if visit and visit > today:
            problems.append("last_visit is in the future")

        if problems:
            patient["problem"] = "; ".join(problems)
            segments["needs_review"].append(patient)
            continue

        seen_phones[phone_key] = patient["name"]
        patient["months"] = months_between(visit, today)
        segments[segment_for(patient["months"], settings)].append(patient)

    return segments, date_warning


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "demo_clinic"
    # Optional fixed "today" (YYYY-MM-DD) so test results don't drift
    today = parse_date(sys.argv[2]) if len(sys.argv) > 2 else date.today()

    settings = load_settings(f"{folder}/settings.json")
    segments, date_warning = load_patients(f"{folder}/patients.csv", settings, today)

    print(f"Clinic: {settings['clinic_name']} | today: {today}")
    if date_warning:
        print()
        print(date_warning)
    print()
    for name in SEGMENTS:
        print(f"{name}: {len(segments[name])}")
        for p in segments[name]:
            if name == "needs_review":
                print(f"    {p['name'] or '(no name)'}: {p['problem']}")
            else:
                print(f"    {p['name']}: {p['months']} months")


if __name__ == "__main__":
    main()