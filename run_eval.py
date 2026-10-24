import os
import re
import sys
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from itertools import combinations

from read_leads import load_leads, write_message
from eval_messages import CHECKS

RUNS_PER_LEAD = 5


def similarity(a, b):
    # 0.0 = nothing in common, 1.0 = identical text
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def final_question(message):
    text = " ".join(message.split())
    parts = re.split(r"(?<=[.!])\s+", text)
    return parts[-1].strip().lower()


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    segments = load_leads()
    hot = segments["hot"]
    review_count = len(segments["needs_review"])

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
                message = write_message(lead["name"], lead["days"],
                                        lead["service"], lead["quote_sent"])
            except Exception as error:
                errors += 1
                print(f"  API error, skipping this one: {error}")
                continue

            passed = {name: check(message, lead) for name, check in CHECKS}
            results.append({"lead": lead, "run": run,
                            "message": message, "passed": passed})

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
    if review_count:
        lines.append(f"Note: {review_count} row(s) in leads.csv went to needs_review and were not scored")
    lines.append("")

    lines.append("Pass rate per check:")
    for name, _ in CHECKS:
        n = sum(1 for r in results if r["passed"][name])
        lines.append(f"  {name:<16} {n}/{scored}  ({100 * n / scored:.0f}%)")
    all_pass = sum(1 for r in results if all(r["passed"].values()))
    lines.append(f"  {'ALL checks':<16} {all_pass}/{scored}  ({100 * all_pass / scored:.0f}%)")
    lines.append("")

    lines.append("Repetition: how alike each lead's messages are (lower = more varied)")
    every_score = []
    for lead in hot:
        msgs = [r["message"] for r in results if r["lead"]["name"] == lead["name"]]
        scores = [similarity(a, b) for a, b in combinations(msgs, 2)]
        if scores:
            every_score.extend(scores)
            lines.append(f"  {lead['name']:<10} average {100 * sum(scores) / len(scores):.0f}%"
                         f"   most alike pair {100 * max(scores):.0f}%")
    if every_score:
        lines.append(f"  {'OVERALL':<10} average {100 * sum(every_score) / len(every_score):.0f}%")
    lines.append("")

    lines.append("Most common closing questions:")
    endings = Counter(final_question(r["message"]) for r in results)
    for question, n in endings.most_common(3):
        lines.append(f"  {n}x  {question}")
    lines.append("")
    lines.append("=" * 60)

    for r in results:
        lead = r["lead"]
        failed = [name for name, ok in r["passed"].items() if not ok]
        status = "PASS" if not failed else "FAIL: " + ", ".join(failed)
        lines.append("")
        lines.append(f"{lead['name']} ({lead['days']} days, {lead['service']}, "
                     f"quote sent: {lead['quote_sent']}) run {r['run']} - {status}")
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