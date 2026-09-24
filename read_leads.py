import csv

with open("leads.csv") as f:
    reader = csv.DictReader(f)
    leads = list(reader)

for lead in leads:

    days = int(lead["days_since_contact"])

    if days < 60:
        print(f"{lead["name"]} : Hot - call this one")

    elif days < 180:
        print(f"{lead["name"]} : Warm - send a message")

    else:
        print(f"{lead["name"]} : Cold - send a message")
