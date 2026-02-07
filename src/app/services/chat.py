from typing import AsyncGenerator
# ALTERAÇÃO: Importando o logger estruturado SOTA
from src.app.core.logging import logger
from src.app.services.llm import llm_service
from src.app.services.router import router_service
from src.app.services.memory import memory_service
from src.app.rag.retriever import vector_store  # Motor de Busca Vetorial
from src.app.services.cache import cache_service
from src.app.prompts.templates import (
    get_system_prompt,
    get_few_shot_messages,
    build_elite_mcp  # Framework de MCP Dinâmico
)

class ChatService:
    async def process_message(
        self,
        user_message: str,
        session_id: str,
        student_level: str = "beginner"
    ) -> AsyncGenerator[str, None]:
        """
        Orquestrador Principal:
        1. Verifica Cache Semântico (Resposta Imediata).
        2. Roteia a intenção.
        3. Realiza busca RAG (Recuperação de Conhecimento).
        4. Recupera o histórico do Redis.
        5. Invoca o LLM em Streaming e persiste os dados.
        """

        # --- CONFIGURAÇÃO DE LOG ESTRUTURADO (Observabilidade SOTA) ---
        # Vincula o session_id a todos os logs gerados nesta execução
        log = logger.bind(session_id=session_id, student_level=student_level)

        # --- 0. CACHE SEMÂNTICO (Camada de Hiper-Velocidade) ---
        await cache_service.create_index()

        cached_response = await cache_service.check_cache(user_message)
        if cached_response:
            log.info("🚀 [SOTA] CACHE HIT", query=user_message[:30])
            yield cached_response

            # PERSISTÊNCIA NA MEMÓRIA DE SESSÃO
            await memory_service.add_message(session_id, "user", user_message)
            await memory_service.add_message(session_id, "assistant", cached_response)

            return

        # --- 1. ROTEAMENTO SEMÂNTICO ---
        intent = await router_service.decide(user_message)
        log.info("✨ Intenção detectada", intent=intent)

        # --- 2. RECUPERAÇÃO DE CONHECIMENTO (RAG) ---
        knowledge_context = []
        if intent == "rag_ingles":
            knowledge_context = await vector_store.search(user_message)
            log.info("📚 Busca RAG realizada", items_found=len(knowledge_context))

        # --- 3. RECUPERAÇÃO DE MEMÓRIA (Redis) ---
        history = await memory_service.get_history(session_id)

        # --- 4. ENGENHARIA DE CONTEXTO (TEMPLATES & MCP) ---
        context_data = build_elite_mcp(
            base_level=student_level,
            retrieved_context=knowledge_context
        )

        system_instructions = get_system_prompt(
            level=student_level,
            context=context_data
        )

        # --- 5. CONSTRUÇÃO DO PAYLOAD ---
        messages = [{"role": "system", "content": system_instructions}]
        messages.extend(get_few_shot_messages(level=student_level))
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # --- 6. GERAÇÃO DA RESPOSTA (LLM) ---
        full_response = ""
        try:
            log.info("🧠 Iniciando inferência no LLM")
            async for chunk in llm_service.chat_stream(messages):
                full_response += chunk
                yield chunk

            # --- 7. PERSISTÊNCIA SOTA ---
            if full_response.strip():
                await cache_service.save_cache(user_message, full_response)
                await memory_service.add_message(session_id, "user", user_message)
                await memory_service.add_message(session_id, "assistant", full_response)
                log.info("💾 Estado sincronizado no Redis")

        except Exception as e:
            log.error("❌ Erro no fluxo de orquestração", error=str(e))
            yield "I'm sorry, I couldn't process that. Please try again."

# Instância Singleton do Orquestrador
chat_service = ChatService()
