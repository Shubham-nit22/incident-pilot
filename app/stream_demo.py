import os

import httpx
from dotenv import load_dotenv

load_dotenv()

with httpx.stream(
    "POST",
    "http://127.0.0.1:8000/incidents/stream",
    headers={"X-API-Key": os.environ["GEMINI_API_KEY"]},
    json={"text": "Our checkout API started returning 500 errors right after the latest deploy."},
    timeout=180,
) as response:
    for line in response.iter_lines():
        if line:
            print(line)