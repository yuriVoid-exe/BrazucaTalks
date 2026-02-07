import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import httpx

from src.app.core.logging import setup_logging
from src.app.api.routes import chat, audio
from src.app.core.config import settings
from src.app.api.routes import chat

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("brazuka_core")

# Ciclo de vida (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Ciclo de vida da aplicação.
  Executa antes de começar a aceitar requisições.
  """
  logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION} no ambiente {settings.ENV_MODE}")

  # 1. Smoke Test do Ollama (Verifica se a IA está rodando)
  try:
    async with httpx.AsyncClient() as client:
      resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
      if resp.status_code == 200:
        models = [m['name'] for m in resp.json()['models']]
        logger.info(f"✅ Ollama Conectado! Modelos disponíveis: {models}")

        # Verifica se o modelo escolhido está lá
        if settings.MODEL_NAME not in str(models):
          logger.warning(f"⚠️ Modelo '{settings.MODEL_NAME}' não encontrado no Ollama! Execute 'ollama pull {settings.MODEL_NAME}'")
      else:
        logger.error(f"❌ Ollama respondeu com erro: {resp.status_code}")
  except Exception as e:
    logger.critical(f"❌ FALHA CRÍTICA: Não foi possível conectar ao Ollama em {settings.OLLAMA_BASE_URL}. Verifique se ele está rodando. Erro: {e}")

  yield

  logger.info("🛑 Desligando aplicação...")

setup_logging()

# Inicialização do App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Registro de Rotas
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["Chat"])
app.include_router(audio.router, prefix=f"{settings.API_V1_STR}/audio", tags=["Audio"])

# Rota de Saúde (Health Check)
@app.get("/health")
async def health_check():
  return {
      "status": "online",
      "app": settings.PROJECT_NAME,
      "model_target": settings.MODEL_NAME,
      "mode": "distributed_mvp"
  }

# Endpoint de teste rápido (só pra você ver a IA funcionando no navegador)
@app.get("/test-ai")
async def test_ai_connection():
    """Rota temporária para testar geração de texto"""
    import ollama
    try:
        # Nota: Em produção, isso ficará em app/services/llm.py
        response = ollama.chat(model=settings.MODEL_NAME, messages=[
            {'role': 'user', 'content': 'Diga "Olá, BrazucaTalks está online!" em inglês.'},
        ])
        return {"response": response['message']['content']}
    except Exception as e:
        return {"error": str(e)}
