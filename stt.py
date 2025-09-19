import tempfile, os
from openai import OpenAI

async def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    p = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    p.write(audio_bytes)
    p.flush(); p.close()
    res = client.audio.transcriptions.create(file=open(p.name, 'rb'), model='whisper-1')
    text = res.text
    os.unlink(p.name)
    return text
