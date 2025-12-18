"""
PDF экстрактор для НПА документов

Использует:
- PyMuPDF (fitz) для базового извлечения текста
- pymupdf4llm для Markdown-friendly формата
"""

from pathlib import Path
from typing import Dict, Any, Optional
import fitz  # PyMuPDF

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False

from ..utils.logger import logger
from ..utils.text_cleaner import TextCleaner


class PDFExtractor:
    """
    Извлечение текста и структуры из PDF файлов НПА

    Возможности:
    - Извлечение текста с сохранением форматирования
    - Markdown-friendly вывод для RAG
    - Очистка от артефактов PDF
    """

    def __init__(self, use_markdown_mode: bool = True, clean_text: bool = True):
        """
        Инициализация экстрактора

        Args:
            use_markdown_mode: Использовать pymupdf4llm для Markdown (если доступен)
            clean_text: Очищать текст от артефактов
        """
        self.use_markdown_mode = use_markdown_mode and HAS_PYMUPDF4LLM
        self.clean_text = clean_text
        self.text_cleaner = TextCleaner() if clean_text else None

        logger.info(
            f"PDFExtractor инициализирован "
            f"(markdown_mode={self.use_markdown_mode}, clean={clean_text})"
        )

        if use_markdown_mode and not HAS_PYMUPDF4LLM:
            logger.warning(
                "pymupdf4llm не установлен. Используется базовый режим. "
                "Установите: pip install pymupdf4llm"
            )

    def extract(self, pdf_path: str) -> Dict[str, Any]:
        """
        Извлечение текста из PDF

        Args:
            pdf_path: Путь к PDF файлу

        Returns:
            dict: {
                'text': str,          # Полный текст документа
                'pages': List[str],   # Текст по страницам
                'metadata': dict,     # Метаданные PDF
                'page_count': int     # Количество страниц
            }

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл не является PDF
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF файл не найден: {pdf_path}")

        if pdf_file.suffix.lower() != '.pdf':
            raise ValueError(f"Файл не является PDF: {pdf_path}")

        logger.info(f"Извлечение текста из: {pdf_path}")

        if self.use_markdown_mode:
            return self._extract_with_pymupdf4llm(pdf_path)
        else:
            return self._extract_with_pymupdf(pdf_path)

    def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Извлечение текста с использованием PyMuPDF

        Args:
            pdf_path: Путь к PDF

        Returns:
            dict: Извлечённые данные
        """
        doc = fitz.open(pdf_path)
        pages_text = []
        full_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Очистка текста если включено
            if self.clean_text and self.text_cleaner:
                text = self.text_cleaner.clean(text)

            pages_text.append(text)
            full_text.append(text)

        # Метаданные PDF
        pdf_metadata = doc.metadata

        doc.close()

        result = {
            'text': '\n\n'.join(full_text),
            'pages': pages_text,
            'metadata': pdf_metadata,
            'page_count': len(pages_text)
        }

        logger.info(f"Извлечено {len(pages_text)} страниц (PyMuPDF)")
        return result

    def _extract_with_pymupdf4llm(self, pdf_path: str) -> Dict[str, Any]:
        """
        Извлечение текста с использованием pymupdf4llm (Markdown-friendly)

        Args:
            pdf_path: Путь к PDF

        Returns:
            dict: Извлечённые данные с Markdown форматированием
        """
        logger.info("Использование pymupdf4llm для Markdown-friendly извлечения")

        # Извлечение в Markdown формате
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # Очистка если включено
        if self.clean_text and self.text_cleaner:
            md_text = self.text_cleaner.clean(md_text)

        # Также получаем метаданные через стандартный fitz
        doc = fitz.open(pdf_path)
        pdf_metadata = doc.metadata
        page_count = len(doc)
        doc.close()

        result = {
            'text': md_text,
            'pages': [md_text],  # В Markdown режиме страницы не разделяются
            'metadata': pdf_metadata,
            'page_count': page_count,
            'is_markdown': True  # Флаг что текст в Markdown формате
        }

        logger.info(f"Извлечено {page_count} страниц (pymupdf4llm)")
        return result

    def extract_page_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Извлечение текста из диапазона страниц

        Args:
            pdf_path: Путь к PDF
            start_page: Начальная страница (с 0)
            end_page: Конечная страница (None = до конца)

        Returns:
            dict: Извлечённые данные
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if end_page is None:
            end_page = total_pages

        pages_text = []
        for page_num in range(start_page, min(end_page, total_pages)):
            page = doc[page_num]
            text = page.get_text()

            if self.clean_text and self.text_cleaner:
                text = self.text_cleaner.clean(text)

            pages_text.append(text)

        doc.close()

        return {
            'text': '\n\n'.join(pages_text),
            'pages': pages_text,
            'page_count': len(pages_text),
            'range': (start_page, min(end_page, total_pages))
        }
