import json
from qdrant_client import QdrantClient
from openai import OpenAI
import os
from uuid import uuid4
from sentence_transformers import SentenceTransformer
from qdrant_client.models import VectorParams



COL = 'sales_docs'
qclient = QdrantClient(url=os.getenv('QDRANT_URL'))

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text):
    return model.encode(text).tolist()

#def embed_text(text):
    #client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    #res = client.embeddings.create(input=text, model="text-embedding-3-small")
    #return res.data[0].embedding

def ingest_documents(path):
    try:
        qclient.recreate_collection(
            collection_name=COL,
            vectors_config=VectorParams(size=384, distance="Cosine")  # ✅ for HuggingFace embeddings
        )
    except Exception as e:
        print("Collection recreate error:", e)

    with open(path, 'r', encoding='utf-8') as f:
        if path.endswith(".json"):
            data = json.load(f)
            chunks = [item["text"] for item in data if "text" in item]
        else:
            text = f.read()
            chunks = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]

    if not chunks:
        raise RuntimeError("No valid chunks found in file")

    points = [
        {"id": str(uuid4()), "vector": embed_text(c), "payload": {"text": c}}
        for c in chunks
    ]
    qclient.upsert(collection_name=COL, points=points)
    return len(points)
