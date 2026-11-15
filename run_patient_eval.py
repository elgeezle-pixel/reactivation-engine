import os
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
from patient_checks import check_patient_message

RUNS_PER_PATIENT = 3


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "demo_clinic"
    today = parse_date(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    label = sys.argv[3] if len(sys.argv) > 3 else "run"

    settings = load_settings(f"{folder}/settings.json")
    incentive = load_incentive(settings)
    segments, date_warning = load_patients(f"{folder}/patients.csv", settings, today)

    jobs = []
    for segment in MESSAGE_SEGMENTS:
        offer = offer_for(incentive, segment, today)
        for patient in segments[segment]:
            jobs.append((patient, segment, offer))

    if not jobs:
        print("No patients to message. Nothing to score.")
        return

    total = len(jobs) * RUNS_PER_PATIENT
    results = []
    errors = 0
    count = 0

    for patient, segment, offer in jobs:
        ctx = check_context(patient, settings, offer)
        for run in range(1, RUNS_PER_PATIENT + 1):
            count += 1
            print(f"Generating {count}/{total}: {patient['name']} (run {run})")
            try:
                message = write_patient_message(patient, segment, settings, offer)
            except Exception as error:
                errors += 1
                print(f"  API error, skipping this one: {error}")
                continue
            results.append({
                "patient": patient, "segment": segment, "offer": bool(offer),
                "run": run, "message": message,
                "checks": check_patient_message(message, ctx),
            })

    scored = len(results)
    if scored == 0:
        print("Every API call failed. Check your internet connection and .env key.")
        return

    # Check names in the order they first appear. offer_exact and no_offer
    # only apply to some messages, so each rate counts only the messages
    # that check applies to.
    names = []
    for r in results:
        for name in r["checks"]:
            if name not in names:
                names.append(name)

    now = datetime.now()
    lines = [
        f"Run label: {label}",
        f"Clinic: {settings['clinic_name']} | today used: {today} | run at: {now.strftime('%Y-%m-%d %H:%M')}",
        f"Patients: {len(jobs)} | Messages scored: {scored} of {total}",
    ]
    if errors:
        lines.append(f"WARNING: {errors} API call(s) failed and were not scored")
    if date_warning:
        lines.append(date_warning)
    lines.append("")
    lines.append("Pass rate per check:")
    for name in names:
        relevant = [r for r in results if name in r["checks"]]
        n = sum(1 for r in relevant if r["checks"][name])
        lines.append(f"  {name:<17} {n}/{len(relevant)}  ({100 * n / len(relevant):.0f}%)")
    all_pass = sum(1 for r in results if all(r["checks"].values()))
    lines.append(f"  {'ALL checks':<17} {all_pass}/{scored}  ({100 * all_pass / scored:.0f}%)")
    lines.append("")
    lines.append("=" * 60)

    for r in results:
        failed = [name for name, ok in r["checks"].items() if not ok]
        status = "PASS" if not failed else "FAIL: " + ", ".join(failed)
        p = r["patient"]
        lines.append("")
        lines.append(f"{p['name']} | {r['segment']} | {gap_text(p['months'])} | "
                     f"{'with offer' if r['offer'] else 'no offer'} | run {r['run']} - {status}")
        lines.append(r["message"])

    report = "\n".join(lines)
    print()
    print(report)

    os.makedirs("eval_results", exist_ok=True)
    filename = f"eval_results/{now.strftime('%Y-%m-%d_%H%M')}_patients_{label}.txt"
    with open(filename, "w") as f:
        f.write(report)
    print()
    print(f"Saved to {filename}")


if __name__ == "__main__":
    main()