import requests, os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
r = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": "Bearer " + key}
)
models = r.json()["data"]
free_models = [m["id"] for m in models if ":free" in m["id"].lower()]
print("All free models:")
for m in free_models:
    print(" -", m)
    