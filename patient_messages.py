import os
import sys
from datetime import date, datetime

from dotenv import load_dotenv
from anthropic import Anthropic

from patients import load_settings, load_patients, parse_date

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=4)

MESSAGE_SEGMENTS = ["due", "lapsed", "long_gone"]

SEGMENT_GUIDANCE = {
    "due": "It is about time for their routine check-up. Keep it light and practical.",
    "lapsed": "It has been a while since their last visit. Be warm and welcoming, with no pressure.",
    "long_gone": ("It has been a long time. Be gentle and welcoming. Make no "
                  "assumptions about why they have not come back."),
}


def gap_text(months):
    # Under 2 years: exact months. From 2 years: whole years, rounded down,
    # so "45 months" becomes "more than 3 years", which is true.
    if months < 24:
        return f"{months} months"
    return f"more than {months // 12} years"


def readable_date(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def load_incentive(settings):
    """Check the optional offer in settings. Returns None if there is none.
    Stops the run if the offer is incomplete, so a half-written offer can
    never reach a patient."""
    incentive = settings.get("incentive")
    if not incentive:
        return None
    for key in ["text", "valid_until", "segments"]:
        if key not in incentive:
            raise ValueError(f"incentive in settings is missing '{key}'")
    text = incentive["text"].strip()
    if not text:
        raise ValueError("incentive text in settings is empty")
    try:
        valid_until = datetime.strptime(incentive["valid_until"], "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("incentive valid_until must be written YYYY-MM-DD, e.g. 2026-11-30")
    unknown = [s for s in incentive["segments"] if s not in MESSAGE_SEGMENTS]
    if unknown:
        raise ValueError(f"incentive segments not recognised: {', '.join(unknown)}")
    return {"text": text, "valid_until": valid_until, "segments": incentive["segments"]}


def offer_for(incentive, segment, today):
    # An offer applies only to its chosen segments, and never after it expires.
    if incentive and segment in incentive["segments"] and today <= incentive["valid_until"]:
        return incentive
    return None


def build_patient_prompt(patient, segment, settings, offer):
    name = patient["name"]
    clinic = settings["clinic_name"]
    gap = gap_text(patient["months"])

    if offer:
        offer_rules = f"""- Include this offer word for word, exactly as written:
  "{offer['text']}". Say it is valid until {readable_date(offer['valid_until'])}.
  Do not change, add to, round up or exaggerate the offer.
- Never mention any other offer, discount or price."""
        word_limit = "Under 50 words"
    else:
        offer_rules = "- Never mention offers, discounts, prices or promotions."
        word_limit = "Under 40 words"

    return f"""You write WhatsApp messages for {clinic}, a private dental
clinic in Nigeria. Messages sound like a friendly, professional
receptionist typing on their phone, not a marketing team.

Patient: {name}
Time since their last visit: {gap}
{SEGMENT_GUIDANCE[segment]}

Write a short message inviting {name} to book a visit.

Rules:
- Start with "{settings['greeting']} {name},"
- {word_limit}
- No emoji
- Mention {clinic} by name
- State the time since their last visit using exactly this wording:
  "{gap}". Do not round it or rephrase it.
- You may invite them for a routine check-up. Never mention what they
  came in for before, or any other treatment, procedure, condition or
  symptom.
{offer_rules}
- Never create urgency, and never warn about what could happen to
  their teeth or health.
- Never give medical or dental advice.
- Never mention appointment availability or specific times.
- Never apologise, and never guess why they have not visited.
- Never mention the time of day.
- Do not leave the next step vague, for example "whenever you're ready".
- End with exactly one question that directly invites them to book a
  visit and can be answered yes or no. It must be the last sentence.
  Nothing comes after it.

Return only the message text."""


def write_patient_message(patient, segment, settings, offer):
    prompt = build_patient_prompt(patient, segment, settings, offer)
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "demo_clinic"
    today = parse_date(sys.argv[2]) if len(sys.argv) > 2 else date.today()

    settings = load_settings(f"{folder}/settings.json")
    incentive = load_incentive(settings)
    segments, date_warning = load_patients(f"{folder}/patients.csv", settings, today)

    print(f"Clinic: {settings['clinic_name']} | today: {today}")
    if incentive:
        if today <= incentive["valid_until"]:
            print(f"Offer: \"{incentive['text']}\" until "
                  f"{readable_date(incentive['valid_until'])}, for "
                  f"{', '.join(incentive['segments'])}")
        else:
            print(f"Offer expired on {readable_date(incentive['valid_until'])}, "
                  "so it is not being used")
    if date_warning:
        print(date_warning)
    print()

    for segment in MESSAGE_SEGMENTS:
        offer = offer_for(incentive, segment, today)
        for patient in segments[segment]:
            try:
                message = write_patient_message(patient, segment, settings, offer)
            except Exception as error:
                message = f"[API error: {error}]"
            tag = "with offer" if offer else "no offer"
            print(f"--- {patient['name']} | {segment} | "
                  f"{gap_text(patient['months'])} | {tag} ---")
            print(message)
            print()

    print(f"Skipped: {len(segments['recent'])} recent, "
          f"{len(segments['needs_review'])} need review")


if __name__ == "__main__":
    main()