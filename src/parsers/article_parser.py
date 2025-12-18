"""
Парсер статей НПА

Разбирает текст документа на:
- Главы (если есть)
- Статьи
- Части статей
- Пункты и подпункты
"""

import re
from typing import List, Tuple, Optional

from ..models.article import Article, ArticlePart, Chapter
from ..utils.logger import logger


class ArticleParser:
    """
    Парсинг структуры НПА на статьи и части

    Поддерживает:
    - Разделение по главам
    - Извлечение статей
    - Разбиение статей на части
    """

    # Паттерны для распознавания структуры
    ARTICLE_PATTERN = r'^Статья\s+(\d+(?:\.\d+)?)\.\s*(.+?)$'
    CHAPTER_PATTERN = r'^(Глава|Раздел)\s+([IVXLCDM]+|\d+)\.\s*(.+?)$'
    PART_PATTERN = r'^(\d+)\.\s+(.+?)$'
    SUBPART_PATTERN = r'^\d+\)\s+.+'

    def __init__(self):
        """Инициализация парсера"""
        self.article_regex = re.compile(self.ARTICLE_PATTERN, re.MULTILINE)
        self.chapter_regex = re.compile(self.CHAPTER_PATTERN, re.MULTILINE)
        self.part_regex = re.compile(self.PART_PATTERN, re.MULTILINE)

        logger.info("ArticleParser инициализирован")

    def parse(self, text: str) -> Tuple[List[Chapter], List[Article]]:
        """
        Парсинг текста на главы и статьи

        Args:
            text: Полный текст документа

        Returns:
            tuple: (список глав, список статей без глав)
                Если документ с главами - первый список заполнен
                Если без глав - второй список заполнен
        """
        logger.info("Начало парсинга документа на статьи")

        # Проверяем наличие глав
        has_chapters = bool(self.chapter_regex.search(text))

        if has_chapters:
            chapters = self._parse_with_chapters(text)
            logger.info(f"Найдено {len(chapters)} глав")
            return chapters, []
        else:
            articles = self._parse_articles_only(text)
            logger.info(f"Найдено {len(articles)} статей (без глав)")
            return [], articles

    def _parse_with_chapters(self, text: str) -> List[Chapter]:
        """
        Парсинг документа с главами

        Args:
            text: Текст документа

        Returns:
            List[Chapter]: Список глав со статьями
        """
        chapters = []
        chapter_matches = list(self.chapter_regex.finditer(text))

        for i, match in enumerate(chapter_matches):
            chapter_type = match.group(1)  # "Глава" или "Раздел"
            chapter_num_str = match.group(2)  # Номер главы (римский или арабский)
            chapter_title = match.group(3).strip()

            # Конвертируем римские числа в арабские
            chapter_number = self._roman_to_int(chapter_num_str) if chapter_num_str.isupper() else int(chapter_num_str)

            # Определяем границы главы
            start_pos = match.end()
            end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)

            chapter_text = text[start_pos:end_pos]

            # Парсим статьи в этой главе
            articles = self._parse_articles_from_text(chapter_text, chapter_number, chapter_title)

            chapter = Chapter(
                number=chapter_number,
                title=chapter_title,
                articles=articles
            )
            chapters.append(chapter)

        return chapters

    def _parse_articles_only(self, text: str) -> List[Article]:
        """
        Парсинг статей без глав

        Args:
            text: Текст документа

        Returns:
            List[Article]: Список статей
        """
        return self._parse_articles_from_text(text)

    def _parse_articles_from_text(
        self,
        text: str,
        chapter_number: Optional[int] = None,
        chapter_title: Optional[str] = None
    ) -> List[Article]:
        """
        Извлечение статей из текста

        Args:
            text: Текст для парсинга
            chapter_number: Номер главы (если есть)
            chapter_title: Название главы (если есть)

        Returns:
            List[Article]: Список статей
        """
        articles = []
        article_matches = list(self.article_regex.finditer(text))

        for i, match in enumerate(article_matches):
            article_number = match.group(1)
            article_title = match.group(2).strip()

            # Определяем границы статьи
            start_pos = match.end()
            end_pos = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(text)

            article_text = text[start_pos:end_pos].strip()

            # Парсим части статьи
            parts = self._parse_article_parts(article_text)

            article = Article(
                number=article_number,
                title=article_title,
                parts=parts,
                full_text=article_text,
                chapter_number=chapter_number,
                chapter_title=chapter_title
            )
            articles.append(article)

        return articles

    def _parse_article_parts(self, text: str) -> List[ArticlePart]:
        """
        Парсинг частей статьи

        Args:
            text: Текст статьи

        Returns:
            List[ArticlePart]: Список частей
        """
        parts = []
        lines = text.split('\n')

        current_part_number = None
        current_part_text = []
        subparts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Проверка на часть статьи (начинается с цифры и точки)
            part_match = self.part_regex.match(line)

            if part_match:
                # Сохраняем предыдущую часть
                if current_part_number is not None:
                    part = ArticlePart(
                        number=current_part_number,
                        text=' '.join(current_part_text),
                        subparts=subparts
                    )
                    parts.append(part)

                # Начинаем новую часть
                current_part_number = int(part_match.group(1))
                current_part_text = [part_match.group(2)]
                subparts = []
            elif line and current_part_number is not None:
                # Продолжение текущей части или подпункт
                if re.match(self.SUBPART_PATTERN, line):
                    subparts.append(line)
                else:
                    current_part_text.append(line)

        # Сохраняем последнюю часть
        if current_part_number is not None:
            part = ArticlePart(
                number=current_part_number,
                text=' '.join(current_part_text),
                subparts=subparts
            )
            parts.append(part)

        # Если нет частей, создаём одну часть со всем текстом
        if not parts:
            parts.append(ArticlePart(
                number=1,
                text=text,
                subparts=[]
            ))

        return parts

    def _roman_to_int(self, roman: str) -> int:
        """
        Конвертация римских чисел в арабские

        Args:
            roman: Римское число (I, II, III, IV, V и т.д.)

        Returns:
            int: Арабское число
        """
        roman_values = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }

        total = 0
        prev_value = 0

        for char in reversed(roman):
            value = roman_values.get(char, 0)
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value

        return total
