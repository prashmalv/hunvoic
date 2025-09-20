import os
import requests

STT_PROVIDER = os.getenv("STT_PROVIDER", "deepgram").lower()

async def transcribe_audio_bytes(audio_bytes: bytes, mimetype="audio/wav") -> str:
    if STT_PROVIDER == "deepgram":
        DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")   # 🔑 lazy load here
        if not DEEPGRAM_API_KEY:
            raise RuntimeError("Deepgram API key not set. Please check your .env file")

        url = "https://api.deepgram.com/v1/listen"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": mimetype
        }
        resp = requests.post(url, headers=headers, data=audio_bytes)
        if resp.status_code != 200:
            raise RuntimeError(f"Deepgram STT failed: {resp.text}")
        return resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]

    else:
        raise RuntimeError("STT_PROVIDER not supported or not set")
