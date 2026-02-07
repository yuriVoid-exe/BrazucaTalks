import logging
import numpy as np
import ollama
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from src.app.core.config import settings

# Configuração de Logs
logger = logging.getLogger("brazuka_rag")

class VectorStoreManager:
    def __init__(self):
        # Conexão assíncrona com Redis (decode_responses=False para lidar com bytes de vetores)
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)

        # Cliente para gerar Embeddings (usando o host configurado)
        self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

        # Configurações do Índice SOTA
        self.index_name = "brazuka_knowledge"
        self.embedding_model = "nomic-embed-text"
        self.vector_dim = 768  # Dimensão exata do nomic-embed-text v1.5
        self.distance_metric = "COSINE"  # Melhor métrica para similaridade de texto

    async def create_index(self):
        """
        Cria o índice de busca vetorial no Redis com suporte Híbrido.
        Idempotente: Se já existir, apenas ignora.
        """
        try:
            # 1. Verifica se o índice já existe
            await self.redis.ft(self.index_name).info()
            logger.info("ℹ️ Índice vetorial já existe no Redis.")
        except ResponseError:
            # 2. Se não existir, cria o Schema
            logger.info("⚙️ Criando novo índice Híbrido (Vetorial + Texto)...")

            schema = (
                TagField("topic"),        # Filtro exato (ex: Grammar)
                TextField("content"),     # Busca Full-Text (BM25 - Palavras-chave)
                TextField("metadata"),    # Metadados extras
                VectorField("embedding", "HNSW", { # Algoritmo SOTA para busca rápida
                    "TYPE": "FLOAT32",
                    "DIM": self.vector_dim,
                    "DISTANCE_METRIC": self.distance_metric,
                    "M": 40,              # Otimização: Conexões por nó (Graph)
                    "EF_CONSTRUCTION": 200 # Otimização: Precisão de construção
                })
            )

            definition = IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)

            await self.redis.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            logger.info("✅ Índice 'brazuka_knowledge' criado com sucesso.")

    async def _get_embedding(self, text: str) -> bytes:
        """Gera o vetor numérico (embedding) usando Ollama e converte para bytes."""
        try:
            response = await self.client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            # Converte lista de floats para array numpy float32 e depois para bytes
            return np.array(response["embedding"], dtype=np.float32).tobytes()
        except Exception as e:
            logger.error(f"Erro ao gerar embedding no Ollama: {e}")
            raise

    async def add_document(self, content: str, metadata: dict = {}, topic: str = "general"):
        """Ingere um documento no Redis (Hash + Vetor)."""
        vector_bytes = await self._get_embedding(content)

        # ID único determinístico baseado no conteúdo (evita duplicatas)
        doc_id = f"doc:{hash(content)}"

        mapping = {
            "topic": topic,
            "content": content,
            "metadata": str(metadata),
            "embedding": vector_bytes
        }

        # Salva como HASH no Redis
        await self.redis.hset(doc_id, mapping=mapping)
        logger.debug(f"Documento ingerido: {doc_id}")

    async def search(self, query: str, k: int = 3) -> list[str]:
        """
        Realiza a Busca Vetorial (KNN) para encontrar os contextos mais relevantes.
        Retorna uma lista de strings (conteúdos).
        """
        try:
            # 1. Gera vetor da pergunta
            query_vector = await self._get_embedding(query)

            # 2. Constrói a Query do RediSearch
            # Sintaxe: Retorne os K vizinhos mais próximos ($vec) do campo @embedding
            redis_query = (
                Query(f"*=>[KNN {k} @embedding $vec AS score]")
                .sort_by("score")
                .return_fields("content", "score")
                .dialect(2) # Obrigatório para busca vetorial
            )

            # 3. Executa a busca
            params = {"vec": query_vector}
            results = await self.redis.ft(self.index_name).search(redis_query, query_params=params)

            if not results.docs:
                logger.info(f"Busca RAG retornou vazio para: '{query}'")
                return []

            # 4. Extrai o conteúdo dos documentos encontrados
            # O Redis retorna bytes se decode_responses=False, então decodificamos aqui
            found_docs = []
            for doc in results.docs:
                # Forma robusta de acessar campos no Redis Document
                try:
                    # Tenta acessar como atributo ou como item de dicionário
                    content = getattr(doc, 'content', None) or doc.__dict__.get('content')

                    if content:
                        if isinstance(content, bytes):
                            content = content.decode("utf-8")
                        found_docs.append(content)
                        logger.info(f"🔍 RAG Hit (Score: {doc.score}): {content[:50]}...")
                except Exception as e:
                    logger.error(f"Erro ao extrair campo do documento: {e}")

            return found_docs

        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return []

# Instância Singleton
vector_store = VectorStoreManager()
