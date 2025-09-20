import os
import requests
from google.cloud import texttospeech

def synthesize_text(text: str, out_path="out.mp3"):
    provider = os.getenv("TTS_PROVIDER", "eleven").lower()

    if provider == "google":
        client = texttospeech.TextToSpeechClient.from_service_account_file(
            os.getenv("GOOGLE_TTS_KEY_JSON_PATH")
        )
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-IN", name="en-IN-Wavenet-D")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        with open(out_path, "wb") as f:
            f.write(response.audio_content)
        return out_path

    elif provider == "eleven":
        api_key = os.getenv("ELEVEN_API_KEY")
        voice_id = os.getenv("ELEVEN_VOICE_ID", "2zRM7PkgwBPiau2jvVXc")  # Default: Rachel
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise RuntimeError(f"ElevenLabs TTS error: {response.text}")

        with open(out_path, "wb") as f:
            f.write(response.content)
        return out_path

    else:
        raise RuntimeError("Unsupported TTS provider. Use google or eleven.")

def synthesize_text_stream(text):
    path = synthesize_text(text)
    def iterfile():
        with open(path, "rb") as f:
            data = f.read(4096)
            while data:
                yield data
                data = f.read(4096)
    return iterfile()
