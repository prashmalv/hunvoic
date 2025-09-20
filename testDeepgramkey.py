import os, requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("DEEPGRAM_API_KEY")
print("Loaded key:", key)

url = "https://api.deepgram.com/v1/listen"
headers = {"Authorization": f"Token {key}", "Content-Type": "audio/wav"}
with open("rlaivenuevoice.wav", "rb") as f:
    r = requests.post(url, headers=headers, data=f.read())
print(r.status_code, r.text)
