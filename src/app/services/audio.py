import os
import logging
import asyncio
import uuid
import edge_tts
from pathlib import Path
from faster_whisper import WhisperModel
# ALTERAÇÃO: Importando biblioteca de resiliência SOTA
from tenacity import retry, stop_after_attempt, wait_exponential
from src.app.core.config import settings

logger = logging.getLogger("brazuka_audio")

class AudioService:
    def __init__(self):
        # Configuração do STT (Faster-Whisper) - Otimizado para seu i3
        self.stt_model_size = "small"
        self.stt_model = None # Lazy loading: só carrega quando usar

    def _get_stt_model(self):
        """Carrega o modelo Whisper apenas quando necessário (economiza RAM no boot)"""
        if self.stt_model is None:
            logger.info(f"📥 Carregando modelo STT Whisper ({self.stt_model_size})...")
            # compute_type="int8" reduz o uso de RAM pela metade sem perder precisão
            self.stt_model = WhisperModel(self.stt_model_size, device="cpu", compute_type="int8", cpu_threads=4)
        return self.stt_model

    async def transcribe(self, audio_path: str) -> str:
        """Converte áudio (STT) de forma assíncrona."""
        try:
            model = self._get_stt_model()
            # Whisper é síncrono, então rodamos em uma thread separada para não travar o server
            segments, _ = await asyncio.to_thread(model.transcribe, audio_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return ""

    # --- NOVA ALTERAÇÃO: Helper resiliente para comunicação externa (WSS Microsoft) ---
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _execute_tts(self, text: str, output_path: Path):
        """Executa a síntese de voz com lógica de retry automático."""
        communicate = edge_tts.Communicate(text, "pt-BR-AntonioNeural")
        await communicate.save(str(output_path))

    async def speak(self, text: str) -> str:
        """Gera áudio (TTS) via Edge-TTS (Custo zero de CPU local) com tolerância a falhas."""
        try:
            filename = f"{uuid.uuid4()}.mp3"
            # settings.AUDIO_DIR aponta para ./static/audio
            output_path = settings.AUDIO_DIR / filename

            # Chamada protegida pelo padrão de resiliência
            await self._execute_tts(text, output_path)

            logger.info(f"🔊 Áudio gerado com sucesso: {filename}")
            # Retorna o caminho relativo para o front acessar via /static/audio/...
            return f"/static/audio/{filename}"
        except Exception as e:
            logger.error(f"❌ Falha crítica na síntese de voz após tentativas: {e}")
            return ""

# Instância Singleton
audio_service = AudioService()
