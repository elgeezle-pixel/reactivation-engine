import csv

def write_segment(filename, segment):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "days_since_contact"])
        writer.writeheader()
        writer.writerows(segment)

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

write_segment("hot_leads.csv", hot)
write_segment("warm_leads.csv", warm)
write_segment("cold_leads.csv", cold)
write_segment("needs_review.csv", needs_review)




