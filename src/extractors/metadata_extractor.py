"""
Экстрактор метаданных из текста НПА

Извлекает:
- Тип документа (ФЕДЕРАЛЬНЫЙ ЗАКОН, ПОСТАНОВЛЕНИЕ и т.д.)
- Номер и дату
- Название
- Принявший орган
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.metadata import DocumentMetadata
from ..utils.logger import logger


class MetadataExtractor:
    """
    Извлечение метаданных из текста НПА

    Использует регулярные выражения для поиска:
    - Типа документа
    - Номера
    - Даты принятия
    - Названия
    """

    # Паттерны для распознавания
    PATTERNS = {
        # Типы документов
        'doc_type': r'(ФЕДЕРАЛЬНЫЙ ЗАКОН|ПОСТАНОВЛЕНИЕ ПРАВИТЕЛЬСТВА РФ|ПОСТАНОВЛЕНИЕ|ПРИКАЗ|УКАЗ ПРЕЗИДЕНТА РФ|УКАЗ|РАСПОРЯЖЕНИЕ)',

        # Номер и дата (несколько вариантов)
        'number_date_1': r'от\s+(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})\s*г?\.*\s*N\s*([\d-]+[\w-]*)',
        'number_date_2': r'от\s+(\d{2}\.\d{2}\.\d{4})\s*N\s*([\d-]+[\w-]*)',

        # Название документа (после типа и номера)
        'title': r'(?:ФЕДЕРАЛЬНЫЙ ЗАКОН|ПОСТАНОВЛЕНИЕ|ПРИКАЗ|УКАЗ|РАСПОРЯЖЕНИЕ).*?\n\n(.+?)(?:\n\n|$)',

        # Принявший орган
        'authority': r'(Государственная Дума|Правительство Российской Федерации|Правительство РФ|Президент Российской Федерации|Президент РФ)',
    }

    # Месяцы для парсинга дат
    MONTHS = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }

    def __init__(self):
        """Инициализация экстрактора"""
        # Компиляция паттернов для эффективности
        self.compiled_patterns = {
            key: re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for key, pattern in self.PATTERNS.items()
        }
        logger.info("MetadataExtractor инициализирован")

    def extract(self, text: str, fallback_title: str = "Без названия") -> DocumentMetadata:
        """
        Извлечение метаданных из текста

        Args:
            text: Текст документа (обычно первые 2000-3000 символов)
            fallback_title: Название по умолчанию если не найдено

        Returns:
            DocumentMetadata: Извлечённые метаданные
        """
        logger.info("Извлечение метаданных из текста")

        # Извлечение компонентов
        doc_type = self._extract_doc_type(text)
        number, date = self._extract_number_and_date(text)
        title = self._extract_title(text) or fallback_title
        authority = self._extract_authority(text)

        metadata = DocumentMetadata(
            doc_type=doc_type or "ДОКУМЕНТ",
            number=number or "N/A",
            date=date or datetime.now(),
            title=title,
            authority=authority,
            status="действующий"  # По умолчанию
        )

        logger.info(f"Метаданные извлечены: {doc_type} N {number}")
        return metadata

    def _extract_doc_type(self, text: str) -> Optional[str]:
        """Извлечение типа документа"""
        match = self.compiled_patterns['doc_type'].search(text)
        if match:
            return match.group(1).upper().strip()
        return None

    def _extract_number_and_date(self, text: str) -> tuple[Optional[str], Optional[datetime]]:
        """
        Извлечение номера и даты документа

        Returns:
            tuple: (номер, дата)
        """
        # Попытка с текстовой датой (01 января 2024 г. N 123-ФЗ)
        match = self.compiled_patterns['number_date_1'].search(text)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            number = match.group(4)

            month = self.MONTHS.get(month_name, 1)
            date = datetime(year, month, day)

            return number, date

        # Попытка с числовой датой (01.01.2024 N 123-ФЗ)
        match = self.compiled_patterns['number_date_2'].search(text)
        if match:
            date_str = match.group(1)
            number = match.group(2)

            try:
                date = datetime.strptime(date_str, '%d.%m.%Y')
                return number, date
            except ValueError:
                pass

        return None, None

    def _extract_title(self, text: str) -> Optional[str]:
        """Извлечение названия документа"""
        match = self.compiled_patterns['title'].search(text)
        if match:
            title = match.group(1).strip()
            # Очистка от лишних символов
            title = re.sub(r'\s+', ' ', title)
            # Удаление кавычек если есть
            title = title.strip('"')
            return title
        return None

    def _extract_authority(self, text: str) -> Optional[str]:
        """Извлечение принявшего органа"""
        match = self.compiled_patterns['authority'].search(text)
        if match:
            return match.group(1).strip()
        return None

    def extract_from_dict(self, data: Dict[str, Any]) -> DocumentMetadata:
        """
        Извлечение метаданных из словаря (например, из PDF metadata)

        Args:
            data: Словарь с данными

        Returns:
            DocumentMetadata: Метаданные
        """
        return DocumentMetadata(
            doc_type=data.get('doc_type', 'ДОКУМЕНТ'),
            number=data.get('number', 'N/A'),
            date=data.get('date', datetime.now()),
            title=data.get('title', 'Без названия'),
            authority=data.get('authority'),
            status=data.get('status', 'действующий')
        )
