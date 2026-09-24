import csv

with open("leads.csv") as f:
    reader = csv.DictReader(f)
    leads = list(reader)

hot = []
warm = []
cold = []
needs_review = []

for lead in leads:
    try:
        days = int(lead["days_since_contact"])
    except ValueError:
        needs_review.append(lead)
        continue

    if days < 60:
        hot.append(lead)

    elif days < 180:
        warm.append(lead)

    else:
        cold.append(lead)

print(f"Hot: {len(hot)}")
print(f"Warm: {len(warm)}")
print(f"Cold: {len(cold)}")
print(f"Needs review: {len(needs_review)}")
