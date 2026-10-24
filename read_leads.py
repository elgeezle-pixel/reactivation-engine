import csv
import os
from datetime import datetime

from dotenv import load_dotenv
from anthropic import Anthropic

from eval_messages import failed_checks

load_dotenv()

# max_retries: the SDK automatically retries dropped connections and
# temporary server errors. 4 retries makes a flaky network less likely
# to break a run.
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=4)

REQUIRED_COLUMNS = ["name", "phone", "service", "days_since_contact", "quote_sent"]
REVIEW_COLUMNS = REQUIRED_COLUMNS + ["message", "flags", "approved"]


def classify(days):
    if days < 30:
        return "hot"
    elif days < 180:
        return "warm"
    else:
        return "cold"


def load_leads(path="leads.csv"):
    """Read and clean the lead file. Any row with a problem goes to
    needs_review with a reason, instead of being guessed at."""
    with open(path) as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        columns = [c.strip() for c in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            raise ValueError(f"{path} is missing column(s): {', '.join(missing)}")
        rows = list(reader)

    segments = {"hot": [], "warm": [], "cold": [], "needs_review": []}

    for row in rows:
        row = {(k or "").strip(): v for k, v in row.items()}
        lead = {c: (row.get(c) or "").strip() for c in REQUIRED_COLUMNS}
        lead["quote_sent"] = lead["quote_sent"].lower()

        problems = []
        days = None
        try:
            days = int(lead["days_since_contact"])
        except ValueError:
            problems.append("bad days_since_contact")
        if not lead["name"]:
            problems.append("missing name")
        if not lead["service"]:
            problems.append("missing service")
        if lead["quote_sent"] not in ("yes", "no"):
            problems.append("quote_sent must be yes or no")

        if problems:
            lead["problem"] = "; ".join(problems)
            segments["needs_review"].append(lead)
            continue

        lead["days"] = days
        segments[classify(days)].append(lead)

    return segments


def build_prompt(name, days, service, quote_sent):
    if quote_sent == "yes":
        situation = (
            f"{name} asked us for a quote for {service}, and we sent them "
            f"the quote. Our last contact with them was {days} days ago. "
            "They have not replied since."
        )
        quote_rule = (
            "- Ask whether they have had a chance to look at the quote. "
            "Do not mention the price or any amount."
        )
    else:
        situation = (
            f"{name} asked us about {service}. No quote has been sent. "
            f"Our last contact with them was {days} days ago. "
            "They have not replied since."
        )
        quote_rule = (
            "- Never mention a quote, price, estimate or cost. "
            "Ask whether they still need it done."
        )

    return f"""You write WhatsApp follow-ups for a Nigerian home
services company. Your messages sound like a real person typing on
their phone, not a marketing team.

Situation: {situation}

Write a short follow-up message to {name}.

Rules:
- Under 35 words
- No emoji
- Mention the service ({service}) by name
- Describe the gap as time since we were last in touch, as exactly
  "{days} days", written in digits. Do not say it has been {days} days
  since they asked or since the quote was sent; we only know when we
  last spoke. Do not round it, do not convert it to weeks, and do not
  put "about" or "around" in front of it.
- Ask exactly one question, and make it the last sentence. It must be
  answerable in three words or fewer. Do not offer two options joined
  by "or". Nothing comes after the question.
{quote_rule}
- Never open with "Hope you're doing well" or "I hope this finds you"
- Never use "just following up", "checking in", or "reaching out"
- Never mention the time of day: no "good morning", "good afternoon"
  or "good evening"
- Never apologise, and never say or imply that we were slow, missed
  their message, or failed to respond.
- Never claim any contact with them beyond what the situation above
  states.
- Never mention offers, availability, discounts or promotions. You
  have no information about any of these.

Return only the message text."""


def write_message(name, days, service, quote_sent):
    prompt = build_prompt(name, days, service, quote_sent)
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def write_segment(filename, segment, fieldnames=REQUIRED_COLUMNS):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(segment)


def main():
    segments = load_leads()

    for name in ["hot", "warm", "cold", "needs_review"]:
        print(f"{name}: {len(segments[name])}")
    for lead in segments["needs_review"]:
        print(f"  needs review - {lead['name'] or '(no name)'}: {lead['problem']}")

    write_segment("hot_leads.csv", segments["hot"])
    write_segment("warm_leads.csv", segments["warm"])
    write_segment("cold_leads.csv", segments["cold"])
    write_segment("needs_review.csv", segments["needs_review"],
                  REQUIRED_COLUMNS + ["problem"])

    hot = segments["hot"]
    if not hot:
        print("No hot leads, so no messages to write.")
        return

    print()
    rows = []
    for i, lead in enumerate(hot, 1):
        print(f"Writing {i}/{len(hot)}: {lead['name']}")
        try:
            message = write_message(lead["name"], lead["days"],
                                    lead["service"], lead["quote_sent"])
            flags = ", ".join(failed_checks(message, lead))
        except Exception as error:
            message = ""
            flags = f"API error: {error}"
        row = {c: lead[c] for c in REQUIRED_COLUMNS}
        row.update({"message": message, "flags": flags, "approved": ""})
        rows.append(row)

    os.makedirs("review", exist_ok=True)
    filename = f"review/{datetime.now().strftime('%Y-%m-%d_%H%M')}_review.csv"
    # utf-8-sig so Excel shows apostrophes and naira signs correctly
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    flagged = sum(1 for r in rows if r["flags"])
    print()
    print(f"Wrote {len(rows)} message(s) to {filename}")
    print(f"{flagged} flagged by the checks. Read those first.")
    print("Nothing has been sent. Read every message and put yes or no")
    print("in the 'approved' column. Only send rows marked yes.")


if __name__ == "__main__":
    main()