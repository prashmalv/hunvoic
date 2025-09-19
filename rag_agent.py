from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import os
import requests

class RagAgent:
    def __init__(self):
        self.qdrant = QdrantClient(url=os.getenv('QDRANT_URL'))
        self.collection = 'sales_docs'
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # LLM provider selection from env
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY")
        }

    def _embed(self, text):
        return self.model.encode(text).tolist()

    def retrieve(self, query, top_k=3):
        hits = self.qdrant.search(
            collection_name=self.collection,
            query_vector=self._embed(query),
            limit=top_k
        )
        return [h.payload.get('text') for h in hits]

    def summarize_with_llm(self, query, docs):
        context = "\n---\n".join(docs)
        prompt = f"Answer the user query based on the following context:\n{context}\n\nUser: {query}\nAnswer:"

        try:
            if self.provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=self.api_keys["openai"])
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                response_json = completion.json()
                if "choices" not in response_json or not response_json["choices"]:
                    raise ValueError(f"Unexpected OpenAI response: {response_json}")
                return response_json["choices"][0]["message"]["content"]

            elif self.provider == "deepseek":
                url = "https://api.deepseek.com/chat/completions"
                headers = {"Authorization": f"Bearer {self.api_keys['deepseek']}"}
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                resp = requests.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                response_json = resp.json()
                if "choices" not in response_json or not response_json["choices"]:
                    raise ValueError(f"Unexpected DeepSeek response: {response_json}")
                return response_json["choices"][0]["message"]["content"]

            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_keys["gemini"])
                try:
                    # Use "flash" or leave the model name empty if not required
                    model = genai.GenerativeModel("gemini-1.5-flash")  # Change "flash" if needed
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    print(f"Gemini API Error: {e}")
                    return "Sorry, there was an issue with the Gemini API."

            else:
                return "No valid LLM provider configured."

        except Exception as e:
            print(f"Error in LLM summarization ({self.provider}): {e}")
            return "Sorry, there was an issue with the LLM provider."

    def answer(self, user_text, session_id=None):
        docs = self.retrieve(user_text)
        if not docs:
            return "Sorry, I could not find relevant information."
        return self.summarize_with_llm(user_text, docs)
