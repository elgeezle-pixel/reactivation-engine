def check_length(message):
    words = message.split()
    return len(words) < 35

def check_question(message):
    count = message.count("?")
    return count == 1



print(check_length("Hi Tunde, it has been 12 days since you asked"))
print(check_length("word " * 40))

# Three test prints for check_question

print(check_question("is this ready?")) # one ?
print(check_question('Hello Tunde')) # No ?
print(check_question("what? Really?")) # Two ?s