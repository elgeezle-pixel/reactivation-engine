def check_length(message):
    words = message.split()
    return len(words) < 35

print(check_length("Hi Tunde, it has been 12 days since you asked"))
print(check_length("word " * 40))
