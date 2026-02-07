import logging
import numpy as np
import ollama
from src.app.core.config import settings

logger = logging.getLogger("brazuka_router")

class SemanticRouter:
    def __init__(self):
        # Cliente assíncrono para não bloquear o event loop
        self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

         # SOTA: Utterances mais ricas e específicas para distanciar os vetores
        self.routes = {
            "chitchat": [
                "Hello", "Hi", "How are you?", "Who are you?", "Nice to meet you",
                "What's your name?", "Good morning", "Ola", "Tudo bem", "Oi",
                "Quem é você", "Como vai", "Prazer em conhecer", "Bom dia",
                "E ai", "Beleza", "Tudo joia"
            ],
            "rag_ingles": [
                "How do I use this?", "Grammar rule explanation", "Explain the difference",
                "Check my grammar", "What does this mean?", "Is this correct?",
                "Present perfect usage", "Verb conjugation", "Make vs Do",
                "Como se diz", "Explique a regra", "Diferença entre", "Qual o significado",
                "Minha frase está certa?", "Corrija meu inglês", "Uso do verbo",
                "Explique o tempo verbal", "Como usar make e do"
            ]
        }

        # Palavras-chave que indicam intenção técnica (Boosting)
        self.technical_keywords = [
            "grammar", "rule", "verb", "tense", "pronunciation", "meaning",
            "correct", "difference", "make", "do", "explain", "present",
            "past", "future", "regra", "gramatica", "verbo", "pronuncia",
            "diferença", "explicação", "corrigir", "errado"
        ]

        # Cache para armazenar os centroides (médias matemáticas) de cada rota
        self.route_centroids = {}

    async def _get_embedding(self, text: str):
        """Transforma texto em um vetor numérico usando o modelo nomic."""
        try:
            resp = await self.client.embeddings(model="nomic-embed-text", prompt=text)
            return np.array(resp['embedding'])
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def _cosine_similarity(self, v1, v2):
        """Calcula quão próximos dois vetores estão (1.0 é idêntico, 0.0 é oposto)."""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        return dot_product / (norm_v1 * norm_v2)

    async def _build_centroids(self):
        """
        Calcula a 'média' matemática de cada categoria.
        Isso torna a decisão ultra rápida.
        """
        for route_name, utterances in self.routes.items():
            embeddings = []
            for text in utterances:
                vec = await self._get_embedding(text)
                if vec is not None:
                    embeddings.append(vec)

            if embeddings:
                # O centroide é a média de todos os vetores daquela categoria
                self.route_centroids[route_name] = np.mean(embeddings, axis=0)

        logger.info("✅ Centroides do Roteador Semântico gerados com sucesso.")

    async def decide(self, user_input: str) -> str:
        """
        Decide a rota utilizando Weighted Intent Boosting e Hierarquia de Confiança.
        """
        if not self.route_centroids:
            await self._build_centroids()

        user_vec = await self._get_embedding(user_input)
        if user_vec is None:
            return "chitchat"

        # 1. Cálculo de scores base via Similaridade de Cosseno
        scores = {}
        for route_name, centroid in self.route_centroids.items():
            scores[route_name] = self._cosine_similarity(user_vec, centroid)

        # 2. TÉCNICA SOTA: KEYWORD BOOSTING
        # Analisamos a presença de palavras técnicas para "puxar" a intenção para o RAG
        input_lower = user_input.lower()
        boost = 0.0
        for word in self.technical_keywords:
            if word in input_lower:
                boost += 0.05

        scores["rag_ingles"] += boost

        rag_score = scores.get("rag_ingles", 0)
        chat_score = scores.get("chitchat", 0)

        logger.info(f"📊 Scores Ponderados -> RAG: {rag_score:.2f} | Chat: {chat_score:.2f}")

        # 3. Lógica de Decisão HIERÁRQUICA (Aperto de Parafusos)

        # A: RAG possui evidência fortíssima ou presença clara de termos técnicos
        if rag_score >= 0.80:
            logger.info(f"🎯 Roteamento RAG (Alta Confiança: {rag_score:.2f})")
            return "rag_ingles"

        # B: Se Chitchat for forte e superior ao RAG, tratamos como conversa social
        if chat_score > 0.60 and chat_score > rag_score:
            logger.info(f"💬 Roteamento CHITCHAT (Predomínio Social: {chat_score:.2f})")
            return "chitchat"

        # C: Zona de Dúvida - Se houver qualquer indício técnico (0.55+), o RAG atua como suporte
        if rag_score > 0.75:
            logger.info(f"📚 Roteamento RAG (Dúvida Pedagógica: {rag_score:.2f})")
            return "rag_ingles"

        # D: Fallback de Segurança
        return "chitchat"

# Instância Singleton
router_service = SemanticRouter()
