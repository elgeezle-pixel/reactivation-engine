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


# Tests (expected output in the comment on each line)
print(check_length("Hi Tunde, it has been 12 days since you asked"))  # True
print(check_length("word " * 40))  # False
print(check_question("is this ready?"))  # True
print(check_question("Hello Tunde"))  # False
print(check_question("what? Really?"))  # False
print(check_banned_phrases("Hi Tunde, it has been 12 days since you asked. Still keen?"))  # True
print(check_banned_phrases("Hi Tunde, just following up on your enquiry."))  # False
print(check_banned_phrases("Hi Tunde, Just Following Up on your enquiry."))  # False (capitals)
print(check_banned_phrases("Hope you’re doing well Tunde"))  # False (curly apostrophe)