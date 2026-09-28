import csv
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) 

def write_message(name, days):
    prompt = f"""You write WhatsApp follow-ups for a Nigerian home
services company. Your messages sound like a real person typing on
their phone, not a marketing team.

Write a message to {name}, who enquired {days} days ago and never
replied.

Rules:
- Under 35 words
- No emoji
- Never open with "Hope you're doing well" or "I hope this finds you"
- Never use "just following up", "checking in", or "reaching out"
- Be specific about the gap in time, don't be vague about it
- End with one easy question they can answer in three words
- Never mention offers, availability, discounts or promotions. You have no information 
about any of these.

Return only the message text."""

    response = client.messages.create(
    model= "claude-sonnet-4-5",
    max_tokens = 200,
    messages = [
        {"role": "user", "content": prompt}
    ],
)
  
    return response.content[0].text


def write_segment(filename, segment):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "days_since_contact"])
        writer.writeheader()
        writer.writerows(segment)

def classify(days): 
    if days < 30:
        return "hot"
    elif days < 180:
        return "warm"
    else:
        return "cold"
    
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

for lead in hot:
    message = write_message(lead["name"], lead["days_since_contact"])
    print(f"---{lead['name']}---")
    print(message)
    print()









