from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
from .rag_agent import RagAgent
from .stt import transcribe_audio_bytes
from .tts import synthesize_text_stream
from .qdrant_ingest import ingest_documents
from dotenv import load_dotenv
import tempfile

app = FastAPI()
agent = RagAgent()

# Explicitly load the .env file from the backend folder
#load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv()

#print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

class QueryIn(BaseModel):
    session_id: str
    text: str = None

@app.post('/ingest')
async def ingest(file: UploadFile = File(...)):
    try:
        # Create a temporary file in the system's temp directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmpfile:
            tmpfile.write(await file.read())
            tmpfile_path = tmpfile.name

        # Pass the temporary file path to the ingest_documents function
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
    resp = agent.answer(user_text, session_id=session_id)
    return {'text': resp}

@app.get('/tts')
async def tts_get(text: str):
    stream = synthesize_text_stream(text)
    return StreamingResponse(stream, media_type='audio/wav')
