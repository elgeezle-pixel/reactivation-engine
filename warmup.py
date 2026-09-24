leads = [
    {"name": "Amina", "days_since_contact" :20},
    {"name": "Chinedu","days_since_contact" :200},
    {"name": "Tunde", "days_since_contact" :90},
    {"name": "Ngozi", "days_since_contact" :400},
]

for lead in leads:

    days = int(lead["days_since_contact"])

    if days < 60:
        print(f"{lead["name"]} : Hot - call this one")

    elif days < 180:
        print(f"{lead["name"]} : Warm - send a message")

    else:
        print(f"{lead["name"]} : Cold - send a message")