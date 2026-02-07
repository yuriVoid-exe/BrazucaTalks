import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  # Metadados
  PROJECT_NAME: str
  VERSION:str
  API_V1_STR:str
  ENV_MODE:str

  # IA Configs
  OLLAMA_BASE_URL: str
  MODEL_NAME: str

  # Infra Configs
  REDIS_URL: str

  # Caminhos (Pathlib facilita manipulação)
  AUDIO_DIR: Path

  # Cors (Permite o Frontend React acessar)
  CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

  # Configuração do Pydantic para ler o .env
  model_config = SettingsConfigDict(
      env_file=".env",
      env_ignore_empty=True,
      extra="ignore"
  )

# Instância Singleton
settings = Settings()

# Garante que diretórios essenciais existam ao importar configs
os.makedirs(settings.AUDIO_DIR, exist_ok=True)
