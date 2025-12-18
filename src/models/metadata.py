"""
Модели метаданных для НПА документов
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from dateutil import parser as date_parser


class DocumentMetadata(BaseModel):
    """
    Метаданные НПА документа

    Используется для:
    - YAML frontmatter в Markdown
    - Фильтрация и поиск в векторных БД
    - Метаданные в ML датасетах
    """

    # Основная информация
    doc_type: str = Field(
        ...,
        description="Тип документа: ФЕДЕРАЛЬНЫЙ ЗАКОН, ПОСТАНОВЛЕНИЕ, ПРИКАЗ и т.д."
    )
    number: str = Field(
        ...,
        description="Номер документа (например: 44-ФЗ, 123-П)"
    )
    date: datetime = Field(
        ...,
        description="Дата принятия документа"
    )
    title: str = Field(
        ...,
        description="Полное название документа"
    )

    # Дополнительная информация
    authority: Optional[str] = Field(
        None,
        description="Орган, принявший документ (Государственная Дума, Правительство РФ и т.д.)"
    )
    status: str = Field(
        default="действующий",
        description="Статус документа: действующий, утративший силу, проект"
    )
    version_date: Optional[datetime] = Field(
        None,
        description="Дата редакции документа"
    )

    # Классификация для RAG
    categories: List[str] = Field(
        default_factory=list,
        description="Категории и теги для классификации"
    )
    references: List[str] = Field(
        default_factory=list,
        description="Ссылки на другие НПА"
    )

    # Источник
    source: str = Field(
        default="КонсультантПлюс",
        description="Источник документа"
    )

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        """Нормализация типа документа"""
        return v.upper().strip()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Валидация статуса"""
        valid_statuses = ["действующий", "утративший силу", "проект"]
        v_lower = v.lower()
        if v_lower not in valid_statuses:
            return "действующий"  # По умолчанию
        return v_lower

    @classmethod
    def parse_date(cls, date_str: str) -> datetime:
        """
        Парсинг даты из различных форматов

        Поддерживаемые форматы:
        - DD.MM.YYYY
        - DD месяц YYYY
        - ISO формат
        """
        try:
            # Попытка стандартного парсинга
            return date_parser.parse(date_str, dayfirst=True)
        except Exception:
            # Fallback на текущую дату при ошибке
            return datetime.now()

    def to_yaml_dict(self) -> dict:
        """
        Конвертация в словарь для YAML frontmatter

        Returns:
            dict: Словарь с метаданными для YAML
        """
        return {
            'doc_type': self.doc_type,
            'number': self.number,
            'date': self.date.strftime('%Y-%m-%d'),
            'title': self.title,
            'authority': self.authority,
            'status': self.status,
            'version_date': self.version_date.strftime('%Y-%m-%d') if self.version_date else None,
            'categories': self.categories,
            'references': self.references,
            'source': self.source
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d')
        }
