import csv
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) 

def write_message(name, days):
    prompt = f"""Write a short Whatsapp message to {name}, who enquired about our service {days} ago and never replied. Friendly, Nigerian business tone, under 40 words. No emoji. Return on messages."""

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









