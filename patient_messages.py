import os
import sys
from datetime import date

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


def build_patient_prompt(patient, segment, settings):
    name = patient["name"]
    clinic = settings["clinic_name"]
    gap = gap_text(patient["months"])

    return f"""You write WhatsApp messages for {clinic}, a private dental
clinic in Nigeria. Messages sound like a friendly, professional
receptionist typing on their phone, not a marketing team.

Patient: {name}
Time since their last visit: {gap}
{SEGMENT_GUIDANCE[segment]}

Write a short message inviting {name} to book a visit.

Rules:
- Start with "{settings['greeting']} {name},"
- Under 40 words
- No emoji
- Mention {clinic} by name
- State the time since their last visit using exactly this wording:
  "{gap}". Do not round it or rephrase it.
- You may invite them for a routine check-up. Never mention what they
  came in for before, or any other treatment, procedure, condition or
  symptom.
- Never create urgency, and never warn about what could happen to
  their teeth or health.
- Never give medical or dental advice.
- Never mention offers, discounts, prices or availability.
- Never apologise, and never guess why they have not visited.
- Never mention the time of day.
- Ask exactly one question, and make it the last sentence. It must be
  answerable in three words or fewer. Nothing comes after the question.

Return only the message text."""


def write_patient_message(patient, segment, settings):
    prompt = build_patient_prompt(patient, segment, settings)
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
    segments, date_warning = load_patients(f"{folder}/patients.csv", settings, today)

    if date_warning:
        print(date_warning)
        print()

    for segment in MESSAGE_SEGMENTS:
        for patient in segments[segment]:
            try:
                message = write_patient_message(patient, segment, settings)
            except Exception as error:
                message = f"[API error: {error}]"
            print(f"--- {patient['name']} | {segment} | {gap_text(patient['months'])} ---")
            print(message)
            print()

    print(f"Skipped: {len(segments['recent'])} recent, "
          f"{len(segments['needs_review'])} need review")


if __name__ == "__main__":
    main()