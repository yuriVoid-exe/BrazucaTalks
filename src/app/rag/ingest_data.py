import asyncio
import json
import logging
import os
from pathlib import Path
from src.app.rag.retriever import vector_store
from src.app.utils.converter import convert_to_markdown

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🚀 INGESTION - %(levelname)s - %(message)s')
logger = logging.getLogger("ingestion_pipeline")

async def ingest_json(file_path: Path):
    """Processa arquivos JSON estruturados."""
    try:
        logger.info(f"📂 Processando JSON: {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for item in data:
            # Cria um documento rico semanticamente
            enriched_content = f"TOPIC: {item.get('topic', 'General')}\nCONTENT: {item.get('content', '')}"

            await vector_store.add_document(
                content=enriched_content,
                metadata=item.get('metadata', {}),
                topic="pedagogical_rule"
            )
            count += 1
        logger.info(f"✅ JSON Finalizado: {count} itens inseridos.")
    except Exception as e:
        logger.error(f"Erro no JSON {file_path.name}: {e}")

async def ingest_pdf(file_path: Path):
    """Processa arquivos PDF convertendo para Markdown."""
    try:
        logger.info(f"📄 Processando PDF: {file_path.name}")
        content = convert_to_markdown(file_path)

        if content:
            # Adiciona o nome do arquivo para contexto
            enriched_content = f"SOURCE DOCUMENT: {file_path.name}\n\n{content}"

            await vector_store.add_document(
                content=enriched_content,
                metadata={"source": file_path.name, "type": "pdf_document"},
                topic="grammar_manual"
            )
            logger.info(f"✅ PDF Finalizado: {file_path.name}")
    except Exception as e:
        logger.error(f"Erro no PDF {file_path.name}: {e}")

async def run_ingestion():
    logger.info("Iniciando Pipeline de Ingestão Híbrida (JSON + PDF)...")

    # 1. Garante o índice
    await vector_store.create_index()

    # 2. Localiza a pasta data
    base_path = Path(__file__).parent.parent.parent.parent
    data_dir = base_path / "data"

    if not data_dir.exists():
        logger.error(f"Pasta 'data' não encontrada em: {data_dir}")
        return

    # 3. Itera sobre todos os arquivos da pasta data (e subpastas se quiser)
    # A ordem importa: processa JSONs (regras curtas) primeiro, depois PDFs (conteúdo denso)
    all_files = sorted(list(data_dir.rglob("*.*")))

    for file_path in all_files:
        if file_path.suffix.lower() == ".json":
            await ingest_json(file_path)
        elif file_path.suffix.lower() == ".pdf":
            await ingest_pdf(file_path)
        else:
            logger.debug(f"Ignorando arquivo desconhecido: {file_path.name}")

    logger.info("🎉 Ingestão Híbrida Concluída!")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
