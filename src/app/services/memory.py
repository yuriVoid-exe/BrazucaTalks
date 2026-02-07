import logging
import orjson
from redis.asyncio import Redis
from src.app.core.config import settings

logger = logging.getLogger("brazuka_memory")

class MemoryService:
    def __init__(self):
        # Conexão assíncrona com o Redis
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Tempo de vida da memória (ex: 24 horas de inatividade)
        self.ttl = 86400
        # Limite de mensagens para o contexto (Sliding Window)
        self.window_size = 10

    def _get_key(self, session_id: str) -> str:
        return f"history:{session_id}"

    async def add_message(self, session_id: str, role: str, content: str):
        """Adiciona uma mensagem ao histórico no Redis."""
        key = self._get_key(session_id)
        message = {"role": role, "content": content}

        # 1. Empurra a mensagem para a lista no Redis
        await self.redis.rpush(key, orjson.dumps(message))

        # 2. Mantém apenas as últimas N mensagens (Sliding Window)
        await self.redis.ltrim(key, -self.window_size, -1)

        # 3. Renova o tempo de expiração
        await self.redis.expire(key, self.ttl)

    async def get_history(self, session_id: str) -> list:
        """Recupera o histórico formatado para o LLM."""
        key = self._get_key(session_id)
        raw_history = await self.redis.lrange(key, 0, -1)

        # Converte de JSON (string) para dicionário Python
        return [orjson.loads(msg) for msg in raw_history]

    async def clear_history(self, session_id: str):
        """Apaga o histórico (útil para comandos de reset)."""
        await self.redis.delete(self._get_key(session_id))

# Instância Singleton
memory_service = MemoryService()
