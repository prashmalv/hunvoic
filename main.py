from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os, tempfile, io
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from .rag_agent import RagAgent
from .stt import transcribe_audio_bytes
from .tts import synthesize_text_stream, synthesize_text
from .qdrant_ingest import ingest_documents

# import DB models
from .models import SessionLocal, Conversation

# audio conversion
from pydub import AudioSegment

from fastapi.staticfiles import StaticFiles



app = FastAPI()

# Serve static audio files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Allow frontend requests (demo: all origins allowed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = RagAgent()

# ✅ Explicitly load .env from backend root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print("DEBUG: Loaded STT_PROVIDER =", os.getenv("STT_PROVIDER"))
print("DEBUG: Loaded DEEPGRAM_API_KEY =", os.getenv("DEEPGRAM_API_KEY")[:6] + "..." if os.getenv("DEEPGRAM_API_KEY") else None)

class QueryIn(BaseModel):
    session_id: str
    text: str = None

# Utility: save message to DB
def save_message(session_id, role, text):
    db = SessionLocal()
    msg = Conversation(session_id=session_id, role=role, text=text)
    db.add(msg)
    db.commit()
    db.close()

@app.post('/ingest')
async def ingest(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmpfile:
            tmpfile.write(await file.read())
            tmpfile_path = tmpfile.name

        count = ingest_documents(tmpfile_path)
        return {'status': 'ok', 'ingested_chunks': count}
    except Exception as e:
        import traceback
        print("Ingest error:", e)
        traceback.print_exc()
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/ask')
async def ask(session_id: str = Form(...), audio: UploadFile = File(None), text: str = Form(None)):
    user_text = text
    if audio:
        audio_bytes = await audio.read()
        user_text = await transcribe_audio_bytes(audio_bytes)
    if not user_text:
        return JSONResponse({'error': 'no input'}, status_code=400)

    save_message(session_id, "user", user_text)
    resp = agent.answer(user_text, session_id=session_id)
    save_message(session_id, "agent", resp)

    return {'text': resp}

@app.get('/tts')
async def tts_get(text: str):
    stream = synthesize_text_stream(text)
    return StreamingResponse(stream, media_type='audio/mpeg')

@app.post('/stt')
async def speech_to_text(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    text = await transcribe_audio_bytes(audio_bytes)
    return {"text": text}

@app.post('/export')
async def export_conversation(conv: list[dict], email: str = None):
    filename = f"/tmp/conversation_{uuid4()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in conv:
            f.write(f"{msg['role']}: {msg['text']}\n")
    return {"status": "ok", "file": filename}

# ✅ Updated: real conversation endpoint with audio/webm → wav conversion
@app.post('/ask-voice')
async def ask_voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    # 1. Convert WebM → WAV
    audio_bytes = await audio.read()
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()
    except Exception as e:
        return JSONResponse({"error": f"Audio conversion failed: {e}"}, status_code=400)

    # 2. STT → get user text
    user_text = await transcribe_audio_bytes(wav_bytes)
    save_message(session_id, "user", user_text)

    # 3. Agent answer
    resp_text = agent.answer(user_text, session_id=session_id)
    save_message(session_id, "agent", resp_text)

    # 4. Convert answer to speech & save to temp file
    audio_path = synthesize_text(resp_text)  # returns path of mp3/wav
    audio_filename = f"{uuid4()}.mp3"
    static_dir = Path("static/audio")
    static_dir.mkdir(parents=True, exist_ok=True)
    final_path = static_dir / audio_filename
    os.replace(audio_path, final_path)

    # Return JSON instead of streaming
    return {
        "user_text": user_text,
        "resp_text": resp_text,
        "audio_url": f"/static/audio/{audio_filename}"
    }


# ✅ Get conversation history
@app.get("/history/{session_id}")
def get_history(session_id: str):
    db = SessionLocal()
    msgs = db.query(Conversation).filter(Conversation.session_id == session_id).all()
    db.close()
    return [{"role": m.role, "text": m.text, "time": m.timestamp.isoformat()} for m in msgs]
