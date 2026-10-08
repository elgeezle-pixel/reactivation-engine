import re


def check_length(message):
    words = message.split()
    return len(words) < 35


def check_question(message):
    count = message.count("?")
    return count == 1


BANNED_PHRASES = [
    "hope you're doing well",
    "i hope this finds you",
    "just following up",
    "checking in",
    "reaching out",
]


def check_banned_phrases(message):
    # Lowercase the message so capitals don't matter, and swap curly
    # apostrophes for straight ones so "you’re" still matches "you're".
    text = message.lower().replace("’", "'")
    for phrase in BANNED_PHRASES:
        if phrase in text:
            return False
    return True


def check_time_gap(message, days):
    # True if the message contains the exact number of days as a whole
    # number. \b means "word boundary", so 12 matches "12 days" and
    # "12-day" but not "112" or "120".
    return re.search(rf"\b{days}\b", message) is not None


# Tripwire for invented claims. Your prompt forbids offers, availability,
# discounts and promotions, and an earlier message made up "openings".
INVENTED_CLAIM_WORDS = [
    "offer",
    "discount",
    "promo",
    "availability",
    "available",
    "opening",
    "slots",
    "limited",
    "this week",
]


def check_no_invented_claims(message):
    text = message.lower()
    for word in INVENTED_CLAIM_WORDS:
        if word in text:
            return False
    return True


# Tests (expected output in the comment on each line)
if __name__ == "__main__":

    print(check_length("Hi Tunde, it has been 12 days since you asked"))  # True
    print(check_length("word " * 40))  # False
    print(check_question("is this ready?"))  # True
    print(check_question("Hello Tunde"))  # False
    print(check_question("what? Really?"))  # False
    print(check_banned_phrases("Hi Tunde, it has been 12 days since you asked. Still keen?"))  # True
    print(check_banned_phrases("Hi Tunde, just following up on your enquiry."))  # False
    print(check_banned_phrases("Hi Tunde, Just Following Up on your enquiry."))  # False (capitals)
    print(check_banned_phrases("Hope you’re doing well Tunde"))  # False (curly apostrophe)
    print(check_time_gap("Hi Tunde, it has been 12 days since you asked", 12))  # True
    print(check_time_gap("Hi Tunde, it has been a while since you asked", 12))  # False
    print(check_time_gap("Hi Tunde, it has been 112 days since you asked", 12))  # False (112 is not 12)
    print(check_no_invented_claims("Hi Tunde, it has been 12 days since you asked. Still keen?"))  # True
    print(check_no_invented_claims("Hi Tunde, we have openings this week. Interested?"))  # False
    print(check_no_invented_claims("Hi Tunde, we can offer you a discount."))  # False
    print(check_no_invented_claims("Hi Tunde, are you still available?"))  # False (false alarm, see below)

