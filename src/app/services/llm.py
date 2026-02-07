import logging
import ollama
from typing import AsyncGenerator
from src.app.core.config import settings

logger = logging.getLogger("brazuka_ai")

class LLMService:
  def __init__(self):
    # O cliente oficial do Ollama suporta chamadas assíncronas
    self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
    self.model = settings.MODEL_NAME

  async def chat_stream(self, messages: list) -> AsyncGenerator[str, None]:
    """
    Gera uma resposta em stream (pedacinho por pedacinho).
    Isso melhora a 'Transparencia de Desempenho' para o usuário.
    """

    try:
      async for part in await self.client.chat(
          model=self.model,
          messages=messages,
          stream=True
          ):
        yield part['message']['content']
    except Exception as e:
      logger.error(f"Erro na geração de texto: {e}")
      yield "Sorry, I'm having trouble thinking rigth now. Could you repeat that?"

# Instância Singleton para ser injetada
llm_service = LLMService()

