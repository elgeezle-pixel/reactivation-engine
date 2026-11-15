import csv
import os
import re
import sys
from datetime import date, datetime

from patients import load_settings, load_patients, parse_date
from patient_messages import (
    MESSAGE_SEGMENTS,
    load_incentive,
    offer_for,
    write_patient_message,
    check_context,
    gap_text,
)
from patient_checks import failed_patient_checks

REVIEW_COLUMNS = ["row", "name", "phone", "segment", "time_since_visit",
                  "offer", "message", "flags", "approved"]


def to_whatsapp_number(phone):
    """Convert a Nigerian mobile number to the 234... format WhatsApp links
    need. Returns None if it doesn't look like a Nigerian mobile number."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("234") and len(digits) == 13:
        return digits
    if digits.startswith("0") and len(digits) == 11:
        return "234" + digits[1:]
    # 10 digits starting 7, 8 or 9: a number whose leading 0 was dropped,
    # usually by a spreadsheet
    if len(digits) == 10 and digits[0] in "789":
        return "234" + digits
    return None


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "demo_clinic"
    today = parse_date(sys.argv[2]) if len(sys.argv) > 2 else date.today()

    settings = load_settings(f"{folder}/settings.json")
    incentive = load_incentive(settings)
    segments, date_warning = load_patients(f"{folder}/patients.csv", settings, today)

    if date_warning:
        print(date_warning)
        print()

    rows = []
    api_errors = 0
    check_failures = 0
    phone_problems = 0

    for segment in MESSAGE_SEGMENTS:
        offer = offer_for(incentive, segment, today)
        for patient in segments[segment]:
            print(f"Writing: {patient['name']} ({segment})")
            flags = []

            if not to_whatsapp_number(patient["phone"]):
                flags.append("phone is not a valid Nigerian mobile number")
                phone_problems += 1

            try:
                message = write_patient_message(patient, segment, settings, offer)
                failed = failed_patient_checks(
                    message, check_context(patient, settings, offer))
                if failed:
                    flags.append("failed checks: " + ", ".join(failed))
                    check_failures += 1
            except Exception as error:
                message = ""
                flags.append(f"API error: {error}")
                api_errors += 1

            rows.append({
                "row": patient["row"],
                "name": patient["name"],
                "phone": patient["phone"],
                "segment": segment,
                "time_since_visit": gap_text(patient["months"]),
                "offer": "yes" if offer else "no",
                "message": message,
                "flags": "; ".join(flags),
                "approved": "",
            })

    if not rows:
        print("No patients to message.")
        return

    os.makedirs("review", exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"review/{slug(settings['clinic_name'])}_{stamp}_review.csv"
    # utf-8-sig so Excel shows apostrophes correctly
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"Wrote {len(rows)} message(s) to {filename}")
    print(f"  API errors:      {api_errors}  (re-run to regenerate these)")
    print(f"  Failed checks:   {check_failures}  (read these first)")
    print(f"  Phone problems:  {phone_problems}  (fix the number in the patient file)")
    print(f"  Skipped:         {len(segments['recent'])} recent, "
          f"{len(segments['needs_review'])} need review")
    print()
    print("Nothing has been sent. Read every message, edit any you want,")
    print("and type yes in the 'approved' column for each one to send.")


if __name__ == "__main__":
    main()