import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
# ALTERAÇÃO: Importando os Schemas centralizados (SOTA)
from src.app.schemas.chat import SpeakRequest, TranscribeResponse
from src.app.services.audio import audio_service
from src.app.core.config import settings

router = APIRouter()

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_voice(file: UploadFile = File(...)):
    """Recebe o arquivo .wav do microfone e retorna o texto (STT)"""
    # Cria um nome temporário seguro
    temp_path = settings.AUDIO_DIR / f"input_{uuid.uuid4()}.wav"

    try:
        # 1. Salva o arquivo vindo do Browser no disco
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Chama a IA para transcrever
        text = await audio_service.transcribe(str(temp_path))

        # Retorna seguindo o padrão do Schema de resposta
        return TranscribeResponse(text=text if text else "")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento de áudio: {str(e)}")
    finally:
        # Limpeza de arquivo temporário
        if temp_path.exists():
            temp_path.unlink()

@router.post("/speak")
async def generate_speech(request: SpeakRequest):
    """Recebe texto e retorna a URL do áudio gerado (TTS)"""
    if not request.text:
        raise HTTPException(status_code=400, detail="Texto vazio")

    audio_url = await audio_service.speak(request.text)

    if not audio_url:
        raise HTTPException(status_code=500, detail="Falha ao gerar áudio")

    return {"audio_url": audio_url}
