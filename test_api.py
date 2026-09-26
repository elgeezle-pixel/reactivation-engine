import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model = "claude-sonnet-4-5",
    max_tokens = 100,
    messages = [
        {"role": "user", "content": "Write a one-sentence WhatsApp message to a customer who enquired about a service 3 months ago and never replied."}
    ],
)

print(response.content[0].text)

