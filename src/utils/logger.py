"""
Настройка логирования для K_plus_parcer
"""

from loguru import logger
import sys
from pathlib import Path


def setup_logger(log_file: str = "logs/k_plus_parcer.log", level: str = "INFO"):
    """
    Настройка логирования

    Args:
        log_file: Путь к файлу лога
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    # Создаём директорию для логов если не существует
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Удаляем дефолтный handler
    logger.remove()

    # Console handler с цветным выводом
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # File handler с ротацией
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation="10 MB",  # Ротация при достижении 10 МБ
        retention="1 week",  # Хранить логи неделю
        compression="zip"  # Сжимать старые логи
    )

    logger.info(f"Логирование настроено: {log_file}")


# Инициализация при импорте
setup_logger()

# Экспорт logger для использования в других модулях
__all__ = ["logger", "setup_logger"]
