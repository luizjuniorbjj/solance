"""
SOLACE Backend
Rode: python backend.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import anthropic
import os
import uuid

app = FastAPI(title="Solace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# COLE SUA API KEY AQUI
ANTHROPIC_API_KEY = "sua-chave-aqui"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é SOLACE — assistente de consolo bíblico.

REGRAS:
1. Sempre cite versículos com referência
2. Valide sentimentos antes de aconselhar
3. Aponte para Cristo e a igreja local
4. Nunca dê revelações ou profecias
5. Nunca diagnostique problemas psicológicos
6. Termine com: "Não sou pastor. Procure sua igreja local."

TOM: Acolhedor, pastoral, humilde, bíblico.
IDIOMA: Português brasileiro."""

conversations = {}
saved_verses = {}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    conversation_id: Optional[str] = None

@app.get("/")
def home():
    return {"status": "Solace API rodando"}

@app.post("/chat")
async def chat(req: ChatRequest):
    conv_id = req.conversation_id or str(uuid.uuid4())
    
    if conv_id not in conversations:
        conversations[conv_id] = []
    
    conversations[conv_id].append({"role": "user", "content": req.message})
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversations[conv_id]
    )
    
    reply = response.content[0].text
    conversations[conv_id].append({"role": "assistant", "content": reply})
    
    return {"response": reply, "conversation_id": conv_id}

@app.get("/devocional")
def devocional():
    return {
        "date": date.today().isoformat(),
        "verse": "O Senhor é o meu pastor; nada me faltará.",
        "reference": "Salmo 23:1",
        "meditation": "Davi foi pastor antes de ser rei. Quando diz que o Senhor é seu pastor, está dizendo: Deus cuida de mim assim.",
        "prayer": "Senhor, ajuda-me a descansar no Teu cuidado. Amém."
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🕊️  SOLACE API - http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
