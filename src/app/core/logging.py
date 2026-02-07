import logging
import sys
import structlog
from src.app.core.config import settings

def setup_logging():
    """
    Configura o sistema de Observabilidade do BrazucaTalks.
    Em desenvolvimento: Logs bonitos e coloridos.
    Em produção: Logs estruturados em JSON para análise distribuída.
    """

    # Configuração do processamento do structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.ENV_MODE == "dev":
        # No seu notebook i3: Logs legíveis para humanos
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # No servidor/Docker: JSON para sistemas de monitoramento
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redireciona o logging padrão do Python para o structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

# Instância global para uso nos serviços
logger = structlog.get_logger()
