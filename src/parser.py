"""
Главный класс парсера НПА

Объединяет все компоненты:
- PDFExtractor - извлечение текста из PDF
- MetadataExtractor - извлечение метаданных
- ArticleParser - парсинг статей
- Exporters - экспорт в Markdown и JSON
"""

from pathlib import Path
from typing import Optional, Dict, Any

from .extractors.pdf_extractor import PDFExtractor
from .extractors.metadata_extractor import MetadataExtractor
from .parsers.article_parser import ArticleParser
from .models.document import NPADocument
from .utils.logger import logger


class NPAParser:
    """
    Главный класс для парсинга НПА документов

    Использование:
        parser = NPAParser()
        document = parser.parse('path/to/npa.pdf')

        # Экспорт в Markdown (ПРИОРИТЕТ!)
        document.export_markdown('output/npa.md')

        # Экспорт в JSON
        document.export_json('output/npa.json')

    Возможности:
    - Извлечение текста из PDF (PyMuPDF + pymupdf4llm)
    - Парсинг метаданных (тип, номер, дата, название)
    - Разбиение на структуру (главы, статьи, части)
    - Экспорт в Markdown с YAML frontmatter
    - Экспорт в JSON
    """

    def __init__(
        self,
        use_markdown_mode: bool = True,
        clean_text: bool = True,
        extract_preamble: bool = True
    ):
        """
        Инициализация парсера

        Args:
            use_markdown_mode: Использовать pymupdf4llm для Markdown-friendly извлечения
            clean_text: Очищать текст от артефактов PDF
            extract_preamble: Извлекать преамбулу документа
        """
        self.use_markdown_mode = use_markdown_mode
        self.clean_text = clean_text
        self.extract_preamble = extract_preamble

        # Инициализация компонентов
        self.pdf_extractor = PDFExtractor(
            use_markdown_mode=use_markdown_mode,
            clean_text=clean_text
        )
        self.metadata_extractor = MetadataExtractor()
        self.article_parser = ArticleParser()

        logger.info("NPAParser инициализирован")

    def parse(self, pdf_path: str) -> NPADocument:
        """
        Парсинг PDF документа НПА

        Args:
            pdf_path: Путь к PDF файлу

        Returns:
            NPADocument: Распарсенный документ

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл не является PDF
        """
        pdf_file = Path(pdf_path)
        logger.info(f"Начало парсинга документа: {pdf_path}")

        # 1. Извлечение текста из PDF
        extracted_data = self.pdf_extractor.extract(pdf_path)
        raw_text = extracted_data['text']

        logger.info(f"Извлечено {extracted_data['page_count']} страниц")

        # 2. Извлечение метаданных
        # Используем первые 3000 символов для поиска метаданных
        metadata_text = raw_text[:3000]
        metadata = self.metadata_extractor.extract(metadata_text)

        # 3. Извлечение преамбулы (если есть)
        preamble = self._extract_preamble(raw_text) if self.extract_preamble else ""

        # 4. Парсинг статей и глав
        chapters, articles = self.article_parser.parse(raw_text)

        # 5. Создание документа
        document = NPADocument(
            metadata=metadata,
            preamble=preamble,
            chapters=chapters,
            articles=articles,
            raw_text=raw_text,
            source_file=str(pdf_file.absolute())
        )

        logger.success(f"Документ успешно распарсен: {metadata.doc_type} N {metadata.number}")
        logger.info(f"Статистика: {document.get_statistics()}")

        return document

    def _extract_preamble(self, text: str) -> str:
        """
        Извлечение преамбулы документа

        Преамбула - это текст до первой статьи или главы

        Args:
            text: Полный текст документа

        Returns:
            str: Текст преамбулы
        """
        import re

        # Ищем первую статью или главу
        article_match = re.search(r'^Статья\s+\d+', text, re.MULTILINE)
        chapter_match = re.search(r'^(Глава|Раздел)\s+', text, re.MULTILINE)

        # Берём ближайшее совпадение
        matches = [m for m in [article_match, chapter_match] if m]
        if not matches:
            return ""

        first_match = min(matches, key=lambda m: m.start())

        # Преамбула - это текст до первой статьи/главы
        preamble = text[:first_match.start()].strip()

        # Удаляем заголовок документа (обычно в начале)
        lines = preamble.split('\n')
        # Пропускаем первые несколько строк (тип документа, номер, название)
        preamble_lines = lines[5:] if len(lines) > 5 else lines

        return '\n'.join(preamble_lines).strip()

    def parse_batch(self, pdf_paths: list, output_dir: Optional[str] = None) -> list:
        """
        Массовый парсинг нескольких документов

        Args:
            pdf_paths: Список путей к PDF файлам
            output_dir: Директория для сохранения результатов (если указана)

        Returns:
            list: Список распарсенных документов
        """
        documents = []

        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Обработка документа {i}/{len(pdf_paths)}: {pdf_path}")

            try:
                document = self.parse(pdf_path)
                documents.append(document)

                # Автоматический экспорт если указана директория
                if output_dir:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)

                    # Генерация имени файла
                    safe_name = document.metadata.number.replace('/', '-').replace('\\', '-')

                    # Экспорт в Markdown и JSON
                    document.export_markdown(str(output_path / f"{safe_name}.md"))
                    document.export_json(str(output_path / f"{safe_name}.json"))

            except Exception as e:
                logger.error(f"Ошибка при обработке {pdf_path}: {e}")
                continue

        logger.success(f"Обработано {len(documents)} из {len(pdf_paths)} документов")
        return documents

    def get_info(self) -> Dict[str, Any]:
        """
        Информация о парсере

        Returns:
            dict: Информация о конфигурации и версиях
        """
        return {
            "version": "0.1.0",
            "markdown_mode": self.use_markdown_mode,
            "clean_text": self.clean_text,
            "extract_preamble": self.extract_preamble,
            "components": {
                "pdf_extractor": "PDFExtractor",
                "metadata_extractor": "MetadataExtractor",
                "article_parser": "ArticleParser"
            }
        }
