
import sys
from loguru import logger


logger.remove()


logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)


logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="15 days",
    level="INFO",
    encoding="utf-8"
)

def get_logger():
    return logger
