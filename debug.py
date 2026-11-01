# debug_serper.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("SERPER_API_KEY")
headers = {"X-API-KEY": key, "Content-Type": "application/json"}

endpoints = [
    "https://google.serper.dev/search",
    "https://google.serper.dev/jobs",
    "https://google.serper.dev/jobs/search",
    "https://google.serper.dev/scholar",
]

for url in endpoints:
    try:
        r = requests.post(
            url,
            headers=headers,
            json={"q": "python developer remote", "num": 5},
            timeout=20,
        )
        print(f"{url}")
        print(f"  Status: {r.status_code}")
        preview = r.text[:200].replace("\n", " ")
        print(f"  Body:   {preview}")
        print()
    except Exception as e:
        print(f"{url} → ERROR: {e}\n")