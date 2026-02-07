# src/app/api/routes/chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.app.services.chat import chat_service
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str  # <--- ADICIONADO: Identificador único da conversa
    level: str = "beginner" # <--- ADICIONADO: Nível opcional (padrão iniciante)

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint de chat com streaming.
    Agora passa o session_id para o orquestrador gerenciar a memória no Redis.
    """
    return StreamingResponse(
        chat_service.process_message(
            user_message=request.message,
            session_id=request.session_id, # <--- PASSANDO O ID
            student_level=request.level
        ),
        media_type="text/event-stream"
    )
