import os 
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.environ["GEMINI_API_KEY"]

resp = httpx.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    headers={"x-goog-api-key":key},
    params={"pageSize":200},
    timeout=30,
)
resp.raise_for_status()

for model in resp.json().get("models",[]):
    if "generateContent" in model.get("supportedGenerationMethods",[]):
        print(model["name"].replace("models/",""))
        