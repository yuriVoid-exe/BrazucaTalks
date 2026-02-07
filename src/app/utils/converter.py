import logging
from pathlib import Path
import pymupdf4llm

logger = logging.getLogger("brazuka_converter")

def convert_to_markdown(file_path: Path) -> str:
    """
    Converte PDF para Markdown mantendo tabelas e estrutura.
    Ultra-leve para CPU (não usa OCR pesado).
    """
    try:
        logger.info(f"📄 Convertendo {file_path.name} para Markdown...")
        # pymupdf4llm extrai texto, tabelas e formatação básica
        md_text = pymupdf4llm.to_markdown(str(file_path))
        return md_text
    except Exception as e:
        logger.error(f"Erro ao converter {file_path}: {e}")
        return ""
