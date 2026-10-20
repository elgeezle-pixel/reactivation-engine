import csv
import os
import sys
from datetime import datetime

from read_leads import write_message, classify
from eval_messages import (
    check_length,
    check_question,
    check_banned_phrases,
    check_time_gap,
    check_no_invented_claims,
)

RUNS_PER_LEAD = 5

# Every check gets the same two inputs (message, days) so we can loop
# over them. Checks that don't need "days" simply ignore it.
CHECKS = [
    ("length", lambda message, days: check_length(message)),
    ("one_question", lambda message, days: check_question(message)),
    ("banned_phrases", lambda message, days: check_banned_phrases(message)),
    ("time_gap", lambda message, days: check_time_gap(message, days)),
    ("no_invented", lambda message, days: check_no_invented_claims(message)),
]


def load_hot_leads():
    with open("leads.csv") as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))

    hot = []
    skipped = 0
    for row in rows:
        try:
            days = int(row["days_since_contact"])
        except ValueError:
            skipped += 1
            continue
        if classify(days) == "hot":
            hot.append({"name": row["name"], "days": days})
    return hot, skipped


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    hot, skipped = load_hot_leads()

    if not hot:
        print("No hot leads found in leads.csv. Nothing to score.")
        return

    total = len(hot) * RUNS_PER_LEAD
    results = []
    errors = 0
    count = 0

    for lead in hot:
        for run in range(1, RUNS_PER_LEAD + 1):
            count += 1
            print(f"Generating {count}/{total}: {lead['name']} (run {run})")
            try:
                message = write_message(lead["name"], lead["days"])
            except Exception as error:
                errors += 1
                print(f"  API error, skipping this one: {error}")
                continue

            passed = {}
            for check_name, check in CHECKS:
                passed[check_name] = check(message, lead["days"])

            results.append({
                "name": lead["name"],
                "days": lead["days"],
                "run": run,
                "message": message,
                "passed": passed,
            })

    scored = len(results)
    if scored == 0:
        print("Every API call failed. Check your internet connection and .env key.")
        return

    now = datetime.now()
    lines = []
    lines.append(f"Run label: {label}")
    lines.append(f"Date: {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Hot leads: {len(hot)} | Messages scored: {scored} of {total}")
    if errors:
        lines.append(f"WARNING: {errors} API call(s) failed and were not scored")
    if skipped:
        lines.append(f"Note: {skipped} row(s) in leads.csv had a bad days value and were skipped")
    lines.append("")
    lines.append("Pass rate per check:")
    for check_name, _ in CHECKS:
        n = sum(1 for r in results if r["passed"][check_name])
        lines.append(f"  {check_name:<16} {n}/{scored}  ({100 * n / scored:.0f}%)")
    all_pass = sum(1 for r in results if all(r["passed"].values()))
    lines.append(f"  {'ALL checks':<16} {all_pass}/{scored}  ({100 * all_pass / scored:.0f}%)")
    lines.append("")
    lines.append("=" * 60)

    for r in results:
        failed = [name for name, ok in r["passed"].items() if not ok]
        status = "PASS" if not failed else "FAIL: " + ", ".join(failed)
        lines.append("")
        lines.append(f"{r['name']} ({r['days']} days) run {r['run']} - {status}")
        lines.append(r["message"])

    report = "\n".join(lines)
    print()
    print(report)

    os.makedirs("eval_results", exist_ok=True)
    filename = f"eval_results/{now.strftime('%Y-%m-%d_%H%M')}_{label}.txt"
    with open(filename, "w") as f:
        f.write(report)
    print()
    print(f"Saved to {filename}")


if __name__ == "__main__":
    main()