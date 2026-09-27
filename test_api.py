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

print(write_message("Amina", 20))
print(write_message("Chinedu", 200))





