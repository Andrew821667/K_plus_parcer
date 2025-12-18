"""
Утилиты для очистки и нормализации текста из PDF
"""

import re
from typing import List


class TextCleaner:
    """
    Очистка текста НПА от артефактов PDF

    Удаляет:
    - Водяные знаки КонсультантПлюс
    - Колонтитулы
    - Избыточные пробелы и переносы строк
    - Артефакты форматирования
    """

    # Паттерны для удаления
    WATERMARK_PATTERNS = [
        r'КонсультантПлюс',
        r'www\.consultant\.ru',
        r'Документ предоставлен КонсультантПлюс',
        r'Дата сохранения:.*?\n',
    ]

    HEADER_FOOTER_PATTERNS = [
        r'Страница \d+ из \d+',
        r'\d+\s*$',  # Номера страниц в конце строк
    ]

    def __init__(self):
        """Инициализация очистителя текста"""
        # Компиляция паттернов для эффективности
        self.watermark_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.WATERMARK_PATTERNS]
        self.header_footer_regex = [re.compile(pattern) for pattern in self.HEADER_FOOTER_PATTERNS]

    def clean(self, text: str) -> str:
        """
        Полная очистка текста

        Args:
            text: Исходный текст из PDF

        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""

        # 1. Удаление водяных знаков
        text = self._remove_watermarks(text)

        # 2. Удаление колонтитулов
        text = self._remove_headers_footers(text)

        # 3. Нормализация пробелов
        text = self._normalize_whitespace(text)

        # 4. Очистка переносов строк
        text = self._fix_line_breaks(text)

        return text.strip()

    def _remove_watermarks(self, text: str) -> str:
        """Удаление водяных знаков"""
        for regex in self.watermark_regex:
            text = regex.sub('', text)
        return text

    def _remove_headers_footers(self, text: str) -> str:
        """Удаление колонтитулов"""
        for regex in self.header_footer_regex:
            text = regex.sub('', text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Нормализация пробелов

        - Множественные пробелы -> один пробел
        - Удаление пробелов в конце строк
        """
        # Удаление пробелов в конце строк
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)

        # Множественные пробелы -> один
        text = re.sub(r' {2,}', ' ', text)

        # Пробелы вокруг знаков препинания (только лишние)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        return text

    def _fix_line_breaks(self, text: str) -> str:
        """
        Исправление переносов строк

        - Удаление лишних пустых строк (>2 подряд)
        - Сохранение структурных разделителей
        """
        # Более 3 переносов строк -> 2
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        return text

    def extract_clean_lines(self, text: str) -> List[str]:
        """
        Извлечение очищенных строк

        Args:
            text: Исходный текст

        Returns:
            List[str]: Список непустых строк
        """
        cleaned = self.clean(text)
        lines = [line.strip() for line in cleaned.split('\n')]
        return [line for line in lines if line]

    def remove_specific_pattern(self, text: str, pattern: str) -> str:
        """
        Удаление специфического паттерна

        Args:
            text: Исходный текст
            pattern: Регулярное выражение для удаления

        Returns:
            str: Текст без паттерна
        """
        return re.sub(pattern, '', text, flags=re.IGNORECASE)


# Singleton instance для удобства
_text_cleaner = TextCleaner()


def clean_text(text: str) -> str:
    """
    Быстрый доступ к очистке текста

    Args:
        text: Исходный текст

    Returns:
        str: Очищенный текст
    """
    return _text_cleaner.clean(text)
