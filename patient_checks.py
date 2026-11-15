import re

# Words that suggest the message mentions a treatment, condition or symptom.
# "check-up" is allowed and is deliberately not in this list.
TREATMENT_WORDS = [
    "filling", "fillings", "root canal", "extraction", "extract", "crown",
    "crowns", "braces", "implant", "implants", "whitening", "scaling",
    "polishing", "denture", "dentures", "cavity", "cavities", "decay",
    "gum disease", "gingivitis", "infection", "pain", "toothache",
    "surgery", "x-ray", "x-rays", "bleeding", "wisdom tooth", "wisdom teeth",
]

URGENCY_WORDS = [
    "urgent", "urgently", "asap", "immediately", "don't wait", "do not wait",
    "too late", "risk", "worse", "serious", "damage", "last chance",
    "hurry", "act now",
]

OFFER_WORDS = [
    "discount", "offer", "offering", "promo", "promotion", "free",
    "percent", "% off",
]

AVAILABILITY_WORDS = [
    "slot", "slots", "available", "availability", "opening", "openings",
    "this week", "today", "tomorrow",
]

TIME_OF_DAY_WORDS = ["good morning", "good afternoon", "good evening"]

APOLOGY_WORDS = ["sorry", "apologise", "apologize", "apologies"]


def normalise(text):
    # Lowercase, straight apostrophes, and single spaces, so line breaks
    # and curly quotes don't hide a match.
    return " ".join(text.lower().replace("’", "'").split())


def find_any(text, phrases):
    """Return the first phrase found as a whole word or phrase, else None.
    'pain' matches 'pain' but not 'Spain'."""
    t = normalise(text)
    for phrase in phrases:
        pattern = r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])"
        if re.search(pattern, t):
            return phrase
    return None


def last_sentence(text):
    parts = re.split(r"(?<=[.!])\s+", " ".join(text.split()))
    return parts[-1].lower()


def check_patient_message(message, ctx):
    """ctx holds what the message should contain: name, greeting, clinic,
    gap, and offer_text / offer_date (both None when there is no offer).
    Returns {check name: True/False}."""
    text = message.strip()
    norm = normalise(text)
    limit = 50 if ctx["offer_text"] else 40

    results = {
        "greeting": text.startswith(f"{ctx['greeting']} {ctx['name']},"),
        "length": len(text.split()) < limit,
        "one_question": text.count("?") == 1 and text.endswith("?"),
        "booking_question": "book" in last_sentence(text),
        "time_gap": normalise(ctx["gap"]) in norm,
        "clinic_named": normalise(ctx["clinic"]) in norm,
    }

    if ctx["offer_text"]:
        results["offer_exact"] = (normalise(ctx["offer_text"]) in norm
                                  and normalise(ctx["offer_date"]) in norm)
    else:
        results["no_offer"] = find_any(text, OFFER_WORDS) is None

    results["no_treatment"] = find_any(text, TREATMENT_WORDS) is None
    results["no_urgency"] = find_any(text, URGENCY_WORDS) is None
    results["no_availability"] = find_any(text, AVAILABILITY_WORDS) is None
    results["no_time_of_day"] = find_any(text, TIME_OF_DAY_WORDS) is None
    results["no_apology"] = find_any(text, APOLOGY_WORDS) is None
    return results


def failed_patient_checks(message, ctx):
    return [name for name, ok in check_patient_message(message, ctx).items() if not ok]


if __name__ == "__main__":
    no_offer = {"name": "Tunde", "greeting": "Hi", "clinic": "Bright Smile Dental",
                "gap": "more than 3 years", "offer_text": None, "offer_date": None}
    with_offer = dict(no_offer, offer_text="10% off your next check-up",
                      offer_date="30 November 2026")

    good = ("Hi Tunde,\n\nIt's been more than 3 years since we last saw you at "
            "Bright Smile Dental. We'd love to welcome you back for a routine "
            "check-up.\n\nWould you like to book a visit with us?")
    good_offer = ("Hi Tunde,\n\nIt's been more than 3 years since we last saw you at "
                  "Bright Smile Dental. We're offering 10% off your next check-up, "
                  "valid until 30 November 2026.\n\nWould you like to book a visit with us?")

    tests = [
        ("good, no offer", good, no_offer, "nothing"),
        ("good, with offer", good_offer, with_offer, "nothing"),
        ("mentions a treatment", good.replace("routine check-up", "filling"),
         no_offer, "no_treatment"),
        ("adds urgency", good.replace("check-up.", "check-up. Don't wait."),
         no_offer, "no_urgency"),
        ("weak question", good.replace("Would you like to book a visit with us?",
                                       "Would that work?"),
         no_offer, "booking_question"),
        ("offer inflated", good_offer.replace("10%", "15%"),
         with_offer, "offer_exact"),
        ("offer when none set", good_offer, no_offer, "no_offer"),
        ("wrong gap", good.replace("3 years", "2 years"), no_offer, "time_gap"),
    ]

    for label, message, ctx, expected in tests:
        failed = failed_patient_checks(message, ctx)
        print(f"{label:<22} failed: {', '.join(failed) or 'nothing':<20} (expected: {expected})")