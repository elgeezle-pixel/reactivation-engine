import csv
import html
import sys
from datetime import date
from urllib.parse import quote

from patients import load_settings
from patient_messages import load_incentive, readable_date
from patient_checks import failed_patient_checks
from make_patient_review import to_whatsapp_number


def load_patient_rows(path):
    """Patient file rows keyed by line number, matching patients.py."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()}
                for r in reader]
    return {number: row for number, row in enumerate(rows, start=2)}


def parse_row_number(text):
    # Spreadsheets sometimes turn 3 into 3.0
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def build_page(clinic, to_send, title):
    cards = []
    for i, p in enumerate(to_send, 1):
        warning = ""
        if p["warnings"]:
            warning = (f'<p class="warn">Check before sending: '
                       f'{html.escape(", ".join(p["warnings"]))}</p>')
        cards.append(f"""
<div class="card">
  <h2>{i}. {html.escape(p['name'])}</h2>
  <pre>{html.escape(p['message'])}</pre>
  {warning}
  <a class="btn" href="{html.escape(p['link'])}" target="_blank" rel="noopener">Open in WhatsApp</a>
  <label><input type="checkbox" data-key="{i}"> Sent</label>
</div>""")

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(clinic)} send list</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; background: #f5f5f5;
         margin: 0; padding: 16px; color: #222; }}
  .wrap {{ max-width: 640px; margin: 0 auto; }}
  .card {{ background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 14px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  h1 {{ font-size: 20px; }} h2 {{ font-size: 16px; margin: 0 0 8px; }}
  pre {{ white-space: pre-wrap; font-family: inherit; background: #f0f7f0;
        padding: 10px; border-radius: 8px; margin: 0 0 10px; }}
  .btn {{ display: inline-block; background: #1f8f4e; color: #fff; text-decoration: none;
         padding: 10px 14px; border-radius: 8px; margin-right: 12px; }}
  .warn {{ color: #a33; font-size: 14px; }}
  .note {{ font-size: 14px; color: #555; }}
</style></head>
<body><div class="wrap">
<h1>{html.escape(clinic)}: {len(to_send)} message(s) to send</h1>
<p class="note">{html.escape(title)}. Tap "Open in WhatsApp", check the message, press send,
then tick "Sent". Ticks are remembered in this browser only.</p>
{''.join(cards)}
</div>
<script>
  var page = location.pathname;
  document.querySelectorAll('input[data-key]').forEach(function (box) {{
    var key = page + '#' + box.dataset.key;
    try {{ box.checked = localStorage.getItem(key) === '1'; }} catch (e) {{}}
    box.addEventListener('change', function () {{
      try {{ localStorage.setItem(key, box.checked ? '1' : '0'); }} catch (e) {{}}
    }});
  }});
</script>
</body></html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 make_send_list.py <approved review file> [clinic folder]")
        return
    review_path = sys.argv[1]
    folder = sys.argv[2] if len(sys.argv) > 2 else "demo_clinic"

    settings = load_settings(f"{folder}/settings.json")
    incentive = load_incentive(settings)
    patients_by_row = load_patient_rows(f"{folder}/patients.csv")

    with open(review_path, encoding="utf-8-sig") as f:
        review = [{(k or "").strip(): (v or "") for k, v in r.items()}
                  for r in csv.DictReader(f)]

    to_send = []
    not_approved = 0
    problems = []

    for r in review:
        name = r.get("name", "").strip()
        if r.get("approved", "").strip().lower() != "yes":
            not_approved += 1
            continue

        message = r.get("message", "").strip()
        row_number = parse_row_number(r.get("row"))
        source = patients_by_row.get(row_number)

        if not message:
            problems.append(f"{name}: approved, but the message is empty")
            continue
        if not source:
            problems.append(f"{name}: row {r.get('row')} not found in the patient file")
            continue
        if source.get("name", "").lower() != name.lower():
            problems.append(f"{name}: row {row_number} in the patient file is now "
                            f"'{source.get('name')}'. The file may have changed, so re-run the review.")
            continue
        number = to_whatsapp_number(source.get("phone", ""))
        if not number:
            problems.append(f"{name}: phone in the patient file is not a valid Nigerian mobile number")
            continue

        has_offer = r.get("offer", "").strip().lower() == "yes"
        if has_offer and (not incentive or date.today() > incentive["valid_until"]):
            problems.append(f"{name}: message includes an offer that has expired or been removed")
            continue

        # Re-check the message, because it may have been edited after review.
        ctx = {
            "name": name,
            "greeting": settings["greeting"],
            "clinic": settings["clinic_name"],
            "gap": r.get("time_since_visit", "").strip(),
            "offer_text": incentive["text"] if has_offer else None,
            "offer_date": readable_date(incentive["valid_until"]) if has_offer else None,
        }
        warnings = failed_patient_checks(message, ctx)

        to_send.append({
            "name": name,
            "message": message,
            "warnings": warnings,
            "link": f"https://wa.me/{number}?text={quote(message)}",
        })

    base = review_path[:-4] if review_path.lower().endswith(".csv") else review_path
    out_path = base + "_send.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(build_page(settings["clinic_name"], to_send, f"Built from {review_path}"))

    print(f"Send list: {len(to_send)} message(s) -> {out_path}")
    print(f"  Not approved (blank or no): {not_approved}")
    print(f"  Approved but blocked:       {len(problems)}")
    for p in problems:
        print(f"    - {p}")
    warned = sum(1 for p in to_send if p["warnings"])
    if warned:
        print(f"  Included, with check warnings: {warned} (shown on the page)")


if __name__ == "__main__":
    main()