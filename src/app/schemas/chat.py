from pydantic import BaseModel, Field
from typing import Optional

# Contrato para o Chat
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str
    level: str = "beginner"

# Contrato para o TTS (Texto para Fala)
class SpeakRequest(BaseModel):
    text: str

# Resposta da Transcrição
class TranscribeResponse(BaseModel):
    text: str
