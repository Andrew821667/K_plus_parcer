"""
Модель НПА документа
Главная модель, объединяющая все компоненты
"""

from typing import List, Optional
from pathlib import Path
import json
from pydantic import BaseModel, Field

from .metadata import DocumentMetadata
from .article import Article, Chapter


class NPADocument(BaseModel):
    """
    Модель НПА документа

    Объединяет:
    - Метаданные (для YAML frontmatter и фильтрации)
    - Структуру (главы и статьи)
    - Методы экспорта (Markdown, JSON)

    Использование:
        doc = NPADocument(metadata=..., chapters=...)
        doc.export_markdown('output/44-fz.md')  # ПРИОРИТЕТ!
        doc.export_json('output/44-fz.json')
    """

    metadata: DocumentMetadata = Field(
        ...,
        description="Метаданные документа"
    )

    # Структура документа
    preamble: str = Field(
        default="",
        description="Преамбула документа (вводная часть)"
    )
    chapters: List[Chapter] = Field(
        default_factory=list,
        description="Главы документа (если есть структура по главам)"
    )
    articles: List[Article] = Field(
        default_factory=list,
        description="Статьи документа (если нет разделения по главам)"
    )

    # Исходные данные
    raw_text: str = Field(
        default="",
        description="Исходный текст документа из PDF"
    )
    source_file: Optional[str] = Field(
        None,
        description="Путь к исходному PDF файлу"
    )

    def export_markdown(self, output_path: str) -> str:
        """
        Экспорт в Markdown с YAML frontmatter

        ⭐ ПРИОРИТЕТ #1 - Основной формат для RAG систем!

        Формат:
        ---
        doc_type: ФЕДЕРАЛЬНЫЙ ЗАКОН
        number: 44-ФЗ
        date: 2013-04-05
        title: О контрактной системе...
        ---

        # Федеральный закон от DD.MM.YYYY N XXX-ФЗ

        **Полное название**

        ## Глава 1. НАЗВАНИЕ

        ### Статья 1. Название статьи

        1. Текст части...

        Args:
            output_path: Путь для сохранения Markdown файла

        Returns:
            str: Путь к созданному файлу
        """
        from ..exporters.markdown_exporter import MarkdownExporter

        exporter = MarkdownExporter()
        return exporter.export(self, output_path)

    def export_json(self, output_path: str, indent: int = 2) -> str:
        """
        Экспорт в JSON

        Args:
            output_path: Путь для сохранения JSON файла
            indent: Отступ для читаемости

        Returns:
            str: Путь к созданному файлу
        """
        from ..exporters.json_exporter import JSONExporter

        exporter = JSONExporter(indent=indent)
        return exporter.export(self, output_path)

    def get_statistics(self) -> dict:
        """
        Статистика по документу

        Returns:
            dict: Статистика (количество глав, статей, токенов и т.д.)
        """
        total_articles = len(self.articles) if self.articles else sum(
            len(chapter.articles) for chapter in self.chapters
        )

        total_tokens = 0
        if self.articles:
            total_tokens = sum(article.get_token_estimate() for article in self.articles)
        else:
            total_tokens = sum(
                sum(article.get_token_estimate() for article in chapter.articles)
                for chapter in self.chapters
            )

        return {
            "chapters": len(self.chapters),
            "articles": total_articles,
            "estimated_tokens": total_tokens,
            "has_preamble": bool(self.preamble),
            "doc_type": self.metadata.doc_type,
            "status": self.metadata.status,
        }

    def get_article_by_number(self, article_number: str) -> Optional[Article]:
        """
        Найти статью по номеру

        Args:
            article_number: Номер статьи (например: "1", "2.1")

        Returns:
            Article или None: Найденная статья
        """
        # Поиск в прямом списке статей
        for article in self.articles:
            if article.number == article_number:
                return article

        # Поиск в главах
        for chapter in self.chapters:
            for article in chapter.articles:
                if article.number == article_number:
                    return article

        return None

    def to_dict(self) -> dict:
        """
        Конвертация в словарь для JSON экспорта

        Returns:
            dict: Полное представление документа
        """
        return {
            "metadata": self.metadata.dict(),
            "statistics": self.get_statistics(),
            "preamble": self.preamble,
            "structure": {
                "chapters": [
                    {
                        "number": chapter.number,
                        "title": chapter.title,
                        "articles": [article.dict() for article in chapter.articles]
                    }
                    for chapter in self.chapters
                ] if self.chapters else [],
                "articles": [article.dict() for article in self.articles] if self.articles else []
            }
        }

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "doc_type": "ФЕДЕРАЛЬНЫЙ ЗАКОН",
                    "number": "44-ФЗ",
                    "date": "2013-04-05",
                    "title": "О контрактной системе..."
                },
                "chapters": [],
                "articles": []
            }
        }
