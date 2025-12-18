"""
Markdown экспортер для НПА документов

⭐ ПРИОРИТЕТ #1 - Основной формат для RAG систем!

Создаёт Markdown файлы с:
- YAML frontmatter (метаданные)
- Иерархическая структура (H1, H2, H3)
- Нумерованные списки для частей статей
- Сохранение ссылок и таблиц
"""

from pathlib import Path
from typing import TYPE_CHECKING
import yaml

from ..utils.logger import logger

if TYPE_CHECKING:
    from ..models.document import NPADocument


class MarkdownExporter:
    """
    Экспорт НПА документов в Markdown

    Формат оптимизирован для:
    - Semantic chunking (LangChain MarkdownHeaderTextSplitter)
    - Векторные БД (YAML frontmatter для метаданных)
    - LLM/RAG системы (чистая структура)
    """

    def __init__(self):
        """Инициализация экспортера"""
        logger.info("Инициализация MarkdownExporter")

    def export(self, document: 'NPADocument', output_path: str) -> str:
        """
        Экспорт документа в Markdown

        Args:
            document: НПА документ для экспорта
            output_path: Путь для сохранения файла

        Returns:
            str: Путь к созданному файлу
        """
        logger.info(f"Экспорт документа в Markdown: {output_path}")

        # Генерация содержимого
        content = self._generate_markdown(document)

        # Создание директории если нужно
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Сохранение файла
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.success(f"Markdown файл создан: {output_path}")
        return str(output_file.absolute())

    def _generate_markdown(self, document: 'NPADocument') -> str:
        """
        Генерация полного Markdown документа

        Args:
            document: НПА документ

        Returns:
            str: Markdown содержимое
        """
        parts = []

        # 1. YAML Frontmatter
        parts.append(self._generate_frontmatter(document))
        parts.append("")  # Пустая строка после frontmatter

        # 2. Заголовок документа (H1)
        parts.append(self._generate_title(document))
        parts.append("")

        # 3. Полное название (жирным)
        if document.metadata.title:
            parts.append(f"**{document.metadata.title}**")
            parts.append("")

        # 4. Преамбула (если есть)
        if document.preamble:
            parts.append(document.preamble.strip())
            parts.append("")

        # 5. Структура документа
        if document.chapters:
            # Документ с главами
            for chapter in document.chapters:
                parts.append(chapter.to_markdown())
                parts.append("")
        elif document.articles:
            # Документ без глав (прямо статьи)
            for article in document.articles:
                parts.append(article.to_markdown())
                parts.append("")

        return '\n'.join(parts)

    def _generate_frontmatter(self, document: 'NPADocument') -> str:
        """
        Генерация YAML frontmatter

        Структура:
        ---
        doc_type: ФЕДЕРАЛЬНЫЙ ЗАКОН
        number: 44-ФЗ
        date: 2013-04-05
        title: О контрактной системе...
        authority: Государственная Дума
        status: действующий
        categories: [...]
        references: [...]
        ---

        Args:
            document: НПА документ

        Returns:
            str: YAML frontmatter
        """
        metadata_dict = document.metadata.to_yaml_dict()

        # Удаляем None значения для чистоты
        metadata_dict = {k: v for k, v in metadata_dict.items() if v is not None}

        # Генерация YAML
        yaml_content = yaml.dump(
            metadata_dict,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )

        return f"---\n{yaml_content}---"

    def _generate_title(self, document: 'NPADocument') -> str:
        """
        Генерация главного заголовка (H1)

        Формат: # Федеральный закон от DD.MM.YYYY N XXX-ФЗ

        Args:
            document: НПА документ

        Returns:
            str: Заголовок H1
        """
        doc_type = document.metadata.doc_type
        number = document.metadata.number
        date = document.metadata.date.strftime('%d.%m.%Y')

        return f"# {doc_type} от {date} N {number}"

    def export_batch(self, documents: list, output_dir: str) -> list:
        """
        Массовый экспорт документов

        Args:
            documents: Список НПА документов
            output_dir: Директория для сохранения

        Returns:
            list: Список путей к созданным файлам
        """
        output_paths = []
        output_directory = Path(output_dir)
        output_directory.mkdir(parents=True, exist_ok=True)

        for i, doc in enumerate(documents, 1):
            logger.info(f"Экспорт документа {i}/{len(documents)}")

            # Генерация имени файла из номера документа
            safe_filename = doc.metadata.number.replace('/', '-').replace('\\', '-')
            output_path = output_directory / f"{safe_filename}.md"

            path = self.export(doc, str(output_path))
            output_paths.append(path)

        logger.success(f"Экспортировано {len(documents)} документов в {output_dir}")
        return output_paths
