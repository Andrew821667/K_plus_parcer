"""
JSON экспортер для НПА документов

Создаёт структурированный JSON с полными данными документа
"""

from pathlib import Path
from typing import TYPE_CHECKING
import json

from ..utils.logger import logger

if TYPE_CHECKING:
    from ..models.document import NPADocument


class JSONExporter:
    """
    Экспорт НПА документов в JSON

    Включает:
    - Полные метаданные
    - Структуру документа
    - Статистику
    """

    def __init__(self, indent: int = 2):
        """
        Инициализация экспортера

        Args:
            indent: Отступ для читаемости JSON (по умолчанию 2)
        """
        self.indent = indent
        logger.info(f"Инициализация JSONExporter (indent={indent})")

    def export(self, document: 'NPADocument', output_path: str) -> str:
        """
        Экспорт документа в JSON

        Args:
            document: НПА документ для экспорта
            output_path: Путь для сохранения файла

        Returns:
            str: Путь к созданному файлу
        """
        logger.info(f"Экспорт документа в JSON: {output_path}")

        # Генерация словаря
        data = document.to_dict()

        # Создание директории если нужно
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Сохранение JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=self.indent
            )

        logger.success(f"JSON файл создан: {output_path}")
        return str(output_file.absolute())

    def export_compact(self, document: 'NPADocument', output_path: str) -> str:
        """
        Экспорт в компактный JSON (без отступов)

        Args:
            document: НПА документ
            output_path: Путь для сохранения

        Returns:
            str: Путь к файлу
        """
        old_indent = self.indent
        self.indent = None
        try:
            return self.export(document, output_path)
        finally:
            self.indent = old_indent

    def to_string(self, document: 'NPADocument') -> str:
        """
        Конвертация документа в JSON строку

        Args:
            document: НПА документ

        Returns:
            str: JSON строка
        """
        data = document.to_dict()
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=self.indent
        )
