"""
Модели для статей НПА
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ArticlePart(BaseModel):
    """
    Часть статьи НПА

    Структура:
    - Статья
      - Часть 1
        - Пункт 1)
        - Пункт 2)
      - Часть 2
    """

    number: int = Field(
        ...,
        description="Номер части статьи"
    )
    text: str = Field(
        ...,
        description="Текст части статьи"
    )
    subparts: List[str] = Field(
        default_factory=list,
        description="Подпункты части статьи (пункты с буквами или цифрами)"
    )

    def to_markdown(self, indent_level: int = 0) -> str:
        """
        Конвертация в Markdown

        Args:
            indent_level: Уровень вложенности для списков

        Returns:
            str: Markdown представление части статьи
        """
        indent = "   " * indent_level
        lines = [f"{self.number}. {self.text}"]

        # Добавляем подпункты если есть
        if self.subparts:
            for subpart in self.subparts:
                lines.append(f"{indent}   - {subpart}")

        return '\n'.join(lines)


class Article(BaseModel):
    """
    Статья НПА

    Основная структурная единица законодательного акта
    """

    number: str = Field(
        ...,
        description="Номер статьи (может быть: 1, 2.1, 14.5 и т.д.)"
    )
    title: str = Field(
        ...,
        description="Название статьи"
    )
    parts: List[ArticlePart] = Field(
        default_factory=list,
        description="Части статьи"
    )
    full_text: str = Field(
        default="",
        description="Полный текст статьи"
    )

    # Метаданные для RAG
    chapter_number: Optional[int] = Field(
        None,
        description="Номер главы, к которой относится статья"
    )
    chapter_title: Optional[str] = Field(
        None,
        description="Название главы"
    )

    def to_markdown(self) -> str:
        """
        Конвертация статьи в Markdown

        Формат:
        ### Статья 1. Название статьи

        1. Текст первой части...
        2. Текст второй части...
           - подпункт 1
           - подпункт 2

        Returns:
            str: Markdown представление статьи
        """
        lines = [f"### Статья {self.number}. {self.title}"]
        lines.append("")  # Пустая строка

        if self.parts:
            for part in self.parts:
                lines.append(part.to_markdown())
                lines.append("")  # Пустая строка между частями
        else:
            # Если нет частей, просто выводим полный текст
            lines.append(self.full_text)
            lines.append("")

        return '\n'.join(lines)

    def get_token_estimate(self) -> int:
        """
        Примерная оценка количества токенов в статье

        Используется для chunking в RAG

        Returns:
            int: Примерное количество токенов
        """
        # Грубая оценка: ~4 символа на токен для русского языка
        text_length = len(self.full_text) if self.full_text else sum(len(p.text) for p in self.parts)
        return text_length // 4

    class Config:
        json_schema_extra = {
            "example": {
                "number": "1",
                "title": "Предмет регулирования настоящего Федерального закона",
                "parts": [
                    {
                        "number": 1,
                        "text": "Настоящий Федеральный закон регулирует отношения...",
                        "subparts": []
                    }
                ],
                "chapter_number": 1,
                "chapter_title": "ОБЩИЕ ПОЛОЖЕНИЯ"
            }
        }


class Chapter(BaseModel):
    """
    Глава НПА

    Группирует статьи по тематическим разделам
    """

    number: int = Field(
        ...,
        description="Номер главы"
    )
    title: str = Field(
        ...,
        description="Название главы"
    )
    articles: List[Article] = Field(
        default_factory=list,
        description="Статьи в этой главе"
    )

    def to_markdown(self) -> str:
        """
        Конвертация главы в Markdown

        Формат:
        ## Глава 1. НАЗВАНИЕ ГЛАВЫ

        ### Статья 1. ...
        ### Статья 2. ...

        Returns:
            str: Markdown представление главы
        """
        lines = [f"## Глава {self.number}. {self.title}"]
        lines.append("")  # Пустая строка

        for article in self.articles:
            lines.append(article.to_markdown())

        return '\n'.join(lines)

    def get_article_count(self) -> int:
        """Количество статей в главе"""
        return len(self.articles)
