import csv
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

REQUIRED_COLUMNS = ["name", "phone", "service", "days_since_contact", "quote_sent"]


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
            f"{name} asked us for a quote for {service} {days} days ago. "
            "We sent them the quote. They have not replied since."
        )
        quote_rule = (
            "- Ask whether they have had a chance to look at the quote. "
            "Do not mention the price or any amount."
        )
    else:
        situation = (
            f"{name} asked us about {service} {days} days ago. "
            "They have not replied since. No quote has been sent."
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
- State the time gap as exactly "{days} days", written in digits. Do
  not round it, do not convert it to weeks, and do not put "about" or
  "around" in front of it.
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

    print()
    for lead in segments["hot"]:
        message = write_message(lead["name"], lead["days"],
                                lead["service"], lead["quote_sent"])
        print(f"---{lead['name']} ({lead['service']}, quote sent: {lead['quote_sent']})---")
        print(message)
        print()


if __name__ == "__main__":
    main()

    