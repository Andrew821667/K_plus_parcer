"""
Базовый пример использования K_plus_parcer

Демонстрирует:
1. Парсинг PDF документа НПА
2. Экспорт в Markdown (ПРИОРИТЕТ #1 для RAG систем)
3. Экспорт в JSON
"""

import sys
from pathlib import Path

# Добавляем src в путь для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from k_plus_parcer import NPAParser
from utils.logger import logger


def main():
    """Основной пример использования парсера"""

    print("=" * 80)
    print("K_plus_parcer - Парсер НПА из КонсультантПлюс")
    print("Фокус на ML/RAG: Markdown база знаний и датасеты")
    print("=" * 80)
    print()

    # Инициализация парсера
    # use_markdown_mode=True использует pymupdf4llm для Markdown-friendly извлечения
    parser = NPAParser(use_markdown_mode=True, clean_text=True)
    logger.info("NPAParser инициализирован")

    # Путь к PDF файлу
    # ПРИМЕЧАНИЕ: Замените на путь к вашему PDF файлу НПА
    pdf_path = project_root / "data" / "input" / "sample_npa.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF файл не найден: {pdf_path}")
        print()
        print("Для тестирования поместите PDF файл НПА в:")
        print(f"   {pdf_path}")
        print()
        print("Пример: Федеральный закон 44-ФЗ, любое Постановление Правительства и т.д.")
        print()
        return

    print(f"📄 Парсинг PDF: {pdf_path.name}")
    print()

    try:
        # Парсинг документа
        document = parser.parse(str(pdf_path))

        print("✅ Документ успешно распарсен!")
        print()

        # Вывод информации о документе
        print("📋 Метаданные документа:")
        print(f"   Тип: {document.metadata.doc_type}")
        print(f"   Номер: {document.metadata.number}")
        print(f"   Дата: {document.metadata.date.strftime('%d.%m.%Y')}")
        print(f"   Название: {document.metadata.title}")
        if document.metadata.authority:
            print(f"   Орган: {document.metadata.authority}")
        print()

        # Структура документа
        if document.chapters:
            print(f"📚 Структура:")
            print(f"   Глав: {len(document.chapters)}")
            total_articles = sum(len(ch.articles) for ch in document.chapters)
            print(f"   Статей: {total_articles}")
        elif document.articles:
            print(f"📚 Структура:")
            print(f"   Статей: {len(document.articles)}")
        print()

        # ⭐ ПРИОРИТЕТ #1: Экспорт в Markdown для RAG систем
        markdown_path = project_root / "data" / "output" / "markdown" / f"{pdf_path.stem}.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"⭐ Экспорт в Markdown (ПРИОРИТЕТ #1 для RAG)...")
        document.export_markdown(str(markdown_path))
        print(f"   ✅ Сохранено: {markdown_path}")
        print(f"   Размер: {markdown_path.stat().st_size / 1024:.1f} KB")
        print()

        # Экспорт в JSON
        json_path = project_root / "data" / "output" / "json" / f"{pdf_path.stem}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"📊 Экспорт в JSON...")
        document.export_json(str(json_path))
        print(f"   ✅ Сохранено: {json_path}")
        print(f"   Размер: {json_path.stat().st_size / 1024:.1f} KB")
        print()

        # Информация о использовании
        print("=" * 80)
        print("🎯 Следующие шаги для RAG/ML:")
        print()
        print("1. RAG система:")
        print(f"   - Загрузите {markdown_path.name} в векторную БД")
        print("   - Используйте YAML frontmatter для фильтрации")
        print("   - Чанкинг: 256-512 токенов с 10-20% overlap")
        print()
        print("2. ML обучение:")
        print(f"   - Используйте {json_path.name} для структурированных данных")
        print("   - Генерируйте QA-пары для fine-tuning")
        print("   - Создавайте примеры юридических рассуждений")
        print()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        logger.exception("Ошибка в basic_usage.py")
        raise


def example_with_custom_settings():
    """
    Пример с кастомными настройками
    """

    # Использование без pymupdf4llm (только PyMuPDF)
    parser_simple = NPAParser(use_markdown_mode=False, clean_text=True)

    # Использование без очистки текста
    parser_raw = NPAParser(use_markdown_mode=True, clean_text=False)

    # Для большинства случаев рекомендуется:
    parser_recommended = NPAParser(use_markdown_mode=True, clean_text=True)


if __name__ == "__main__":
    main()
