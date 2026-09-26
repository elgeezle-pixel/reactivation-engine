import csv

def write_segment(filename, segment):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "days_since_contact"])
        writer.writeheader()
        writer.writerows(segment)

def classify(days):
    if days < 60:
        return "hot"
    elif days < 180:
        return "warm"
    else:
        return "hold"
    
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

    segment = classify(days)

    if segment == "hot":
        hot.append(lead)
    elif segment == "warm":
        warm.append(lead)
    else:
        cold.append(lead)

print(f"hot: {len(hot)}")
print(f"warm: {len(warm)}")
print(f"cold: {len(cold)}")
print(f"needs review: {len(needs_review)}")

write_segment("hot_leads.csv", hot)
write_segment("warm_leads.csv", warm)
write_segment("cold_leads.csv", cold)
write_segment("needs_review.csv", needs_review)






