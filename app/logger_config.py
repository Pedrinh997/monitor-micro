import sys
from loguru import logger

logger.remove()  # Remove o handler padrão
logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO")
logger.add("logs/app.log", rotation="10 MB", level="DEBUG")  # Salva logs em arquivo
