import logging
import numpy as np
import orjson
import ollama
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.query import Query
from src.app.core.config import settings

logger = logging.getLogger("brazuka_cache")

class SemanticCache:
    def __init__(self):
        # Inicializa conexão com Redis (modo raw bytes para vetores)
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
        self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

        # Configurações do Índice
        self.index_name = "brazuka_cache"
        self.threshold = 0.35 # Limiar de similaridade (0.0 = idêntico, 0.15 = muito parecido)

    async def create_index(self):
        """
        Cria índice exclusivo para respostas cacheadas no Redis Stack.
        Operação idempotente (segura para rodar múltiplas vezes).
        """
        try:
            await self.redis.ft(self.index_name).info()
        except:
            # Se der erro, é porque o índice não existe. Criamos agora.
            schema = (
                VectorField("embedding", "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": 768,
                    "DISTANCE_METRIC": "COSINE"
                }),
                TagField("response") # Armazena a resposta textual da IA
            )
            await self.redis.ft(self.index_name).create_index(schema)
            logger.info("✅ Índice de Cache Semântico criado.")

    async def check_cache(self, query: str) -> str | None:
        """
        Verifica se existe uma resposta cacheada semanticamente similar.
        Retorna a string da resposta ou None (Cache Miss).
        """
        try:
            # 1. Vetoriza a pergunta atual do usuário
            resp = await self.client.embeddings(model="nomic-embed-text", prompt=query)
            vec = np.array(resp['embedding'], dtype=np.float32).tobytes()

            # 2. Busca no Redis (KNN - Vizinho mais próximo)
            q = Query(f"*=>[KNN 1 @embedding $vec AS score]")\
                .return_fields("response", "score")\
                .dialect(2)

            res = await self.redis.ft(self.index_name).search(q, query_params={"vec": vec})

            # 3. Avalia o resultado
            if res.docs:
                doc = res.docs[0]
                score = float(doc.score)

                # Verifica se a similaridade está dentro do aceitável
                if score < self.threshold:
                    logger.info(f"🚀 CACHE HIT! (Score: {score:.4f})")

                    # --- FIX DE ROBUSTEZ (SOTA) ---
                    # Acesso seguro ao campo 'response' independente do mapeamento do Redis Document
                    raw_content = getattr(doc, 'response', None) or doc.__dict__.get('response')

                    # Garante que funciona tanto se o Redis retornar bytes quanto string
                    if raw_content:
                        if isinstance(raw_content, bytes):
                            return raw_content.decode("utf-8")
                        return str(raw_content)

            logger.info("🐢 CACHE MISS")
            return None

        except Exception as e:
            logger.error(f"Erro ao verificar cache: {e}")
            return None

    async def save_cache(self, query: str, response: str):
        """
        Salva a pergunta (vetor) e a resposta (texto) no Redis.
        Define um TTL para evitar dados obsoletos.
        """
        try:
            resp = await self.client.embeddings(model="nomic-embed-text", prompt=query)
            vec = np.array(resp['embedding'], dtype=np.float32).tobytes()

            # Gera um ID determinístico para a chave
            doc_id = f"cache:{hash(query)}"

            await self.redis.hset(doc_id, mapping={
                "embedding": vec,
                "response": response
            })

            # TTL: Cache expira em 1 hora (3600 segundos)
            # Isso é crucial em sistemas distribuídos para gestão de memória
            await self.redis.expire(doc_id, 3600)

        except Exception as e:
            logger.error(f"Erro ao salvar no cache: {e}")

# Instância Singleton
cache_service = SemanticCache()
