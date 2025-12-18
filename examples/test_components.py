"""
Тестирование компонентов K_plus_parcer без реального PDF

Проверяет работу:
1. MetadataExtractor - извлечение метаданных
2. ArticleParser - парсинг статей
3. MarkdownExporter - экспорт в Markdown
4. JSONExporter - экспорт в JSON
"""

import sys
from pathlib import Path
from datetime import datetime

# Добавляем директорию проекта в путь для импорта k_plus_parcer
project_root = Path(__file__).parent.parent
# Добавляем src как k_plus_parcer
import sys
sys.path.insert(0, str(project_root))

# Используем прямой import из src/ как k_plus_parcer
import src as k_plus_parcer
from src.extractors.metadata_extractor import MetadataExtractor
from src.parsers.article_parser import ArticleParser
from src.exporters.markdown_exporter import MarkdownExporter
from src.exporters.json_exporter import JSONExporter
from src.models.document import NPADocument
from src.models.metadata import DocumentMetadata
from src.models.article import Article, ArticlePart, Chapter
from src.utils.logger import logger


# Пример текста НПА для тестирования
SAMPLE_NPA_TEXT = """
ФЕДЕРАЛЬНЫЙ ЗАКОН

от 5 апреля 2013 г. N 44-ФЗ

О КОНТРАКТНОЙ СИСТЕМЕ В СФЕРЕ ЗАКУПОК ТОВАРОВ, РАБОТ, УСЛУГ
ДЛЯ ОБЕСПЕЧЕНИЯ ГОСУДАРСТВЕННЫХ И МУНИЦИПАЛЬНЫХ НУЖД

Принят Государственной Думой 22 марта 2013 года
Одобрен Советом Федерации 27 марта 2013 года

Глава 1. ОБЩИЕ ПОЛОЖЕНИЯ

Статья 1. Предмет регулирования настоящего Федерального закона

1. Настоящий Федеральный закон регулирует отношения, направленные на обеспечение государственных и муниципальных нужд в целях повышения эффективности, результативности осуществления закупок товаров, работ, услуг, обеспечения гласности и прозрачности осуществления таких закупок.

2. Настоящий Федеральный закон не регулирует отношения, связанные с:
   - куплей-продажей ценных бумаг, валютных ценностей, драгоценных металлов
   - приобретением биржевых товаров на товарной бирже

Статья 2. Основные понятия, используемые в настоящем Федеральном законе

1. Для целей настоящего Федерального закона используются следующие основные понятия:
   - закупка товара, работы, услуги для обеспечения государственных или муниципальных нужд
   - участник закупки - любое юридическое лицо

2. Иные понятия, используемые в настоящем Федеральном законе, применяются в том же значении, что и в других федеральных законах.

Глава 2. ПЛАНИРОВАНИЕ ЗАКУПОК

Статья 3. Планирование закупок

1. Планирование закупок осуществляется исходя из определенных с учетом положений статьи 13 настоящего Федерального закона целей осуществления закупок.

2. Планы закупок формируются на срок, соответствующий сроку действия федерального закона о федеральном бюджете.
"""


def test_metadata_extractor():
    """Тест извлечения метаданных"""
    print("=" * 80)
    print("🧪 Тест 1: MetadataExtractor")
    print("=" * 80)

    extractor = MetadataExtractor()
    metadata = extractor.extract(SAMPLE_NPA_TEXT, fallback_title="Тестовый документ")

    print(f"✅ Тип документа: {metadata.doc_type}")
    print(f"✅ Номер: {metadata.number}")
    print(f"✅ Дата: {metadata.date.strftime('%d.%m.%Y')}")
    print(f"✅ Название: {metadata.title}")

    if metadata.authority:
        print(f"✅ Орган: {metadata.authority}")

    # Проверка что данные извлечены корректно
    assert metadata.doc_type == "ФЕДЕРАЛЬНЫЙ ЗАКОН", "Тип документа не извлечён"
    assert metadata.number == "44-ФЗ", "Номер не извлечён"
    assert metadata.date.year == 2013, "Дата не извлечена"

    print("\n✅ MetadataExtractor работает корректно!\n")
    return metadata


def test_article_parser():
    """Тест парсинга статей"""
    print("=" * 80)
    print("🧪 Тест 2: ArticleParser")
    print("=" * 80)

    parser = ArticleParser()
    chapters, articles = parser.parse(SAMPLE_NPA_TEXT)

    if chapters:
        print(f"✅ Извлечено глав: {len(chapters)}")
        for chapter in chapters:
            print(f"   - Глава {chapter.number}: {chapter.title}")
            print(f"     Статей: {len(chapter.articles)}")
    else:
        print(f"✅ Извлечено статей: {len(articles)}")

    # Проверки
    assert len(chapters) > 0 or len(articles) > 0, "Не извлечены ни главы, ни статьи"

    if chapters:
        total_articles = sum(len(ch.articles) for ch in chapters)
        print(f"\n✅ Всего статей в главах: {total_articles}")
        assert total_articles > 0, "В главах нет статей"

    print("\n✅ ArticleParser работает корректно!\n")
    return chapters, articles


def test_markdown_export(metadata, chapters, articles):
    """Тест экспорта в Markdown"""
    print("=" * 80)
    print("🧪 Тест 3: MarkdownExporter (ПРИОРИТЕТ #1)")
    print("=" * 80)

    # Создаём документ
    document = NPADocument(
        metadata=metadata,
        chapters=chapters,
        articles=articles,
        raw_text=SAMPLE_NPA_TEXT
    )

    # Экспортируем в Markdown
    output_path = project_root / "data" / "output" / "markdown" / "test_sample.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    exporter = MarkdownExporter()
    result_path = exporter.export(document, str(output_path))

    print(f"✅ Markdown экспортирован: {result_path}")

    # Проверяем что файл создан
    assert Path(result_path).exists(), "Markdown файл не создан"

    # Читаем и проверяем содержимое
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем наличие ключевых элементов
    assert "---" in content, "Нет YAML frontmatter"
    assert "doc_type:" in content, "Нет метаданных в frontmatter"
    assert "# Федеральный закон" in content or "# ФЕДЕРАЛЬНЫЙ ЗАКОН" in content, "Нет заголовка H1"
    assert "##" in content, "Нет заголовков H2 (главы)"
    assert "###" in content, "Нет заголовков H3 (статьи)"

    print(f"✅ Размер файла: {len(content)} символов")
    print(f"✅ YAML frontmatter: присутствует")
    print(f"✅ Структура (H1, H2, H3): корректна")

    # Показываем первые 500 символов
    print("\n📄 Первые 500 символов:")
    print("-" * 80)
    print(content[:500])
    print("-" * 80)

    print("\n✅ MarkdownExporter работает корректно!\n")
    return result_path


def test_json_export(metadata, chapters, articles):
    """Тест экспорта в JSON"""
    print("=" * 80)
    print("🧪 Тест 4: JSONExporter")
    print("=" * 80)

    # Создаём документ
    document = NPADocument(
        metadata=metadata,
        chapters=chapters,
        articles=articles,
        raw_text=SAMPLE_NPA_TEXT
    )

    # Экспортируем в JSON
    output_path = project_root / "data" / "output" / "json" / "test_sample.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    exporter = JSONExporter()
    result_path = exporter.export(document, str(output_path))

    print(f"✅ JSON экспортирован: {result_path}")

    # Проверяем что файл создан
    assert Path(result_path).exists(), "JSON файл не создан"

    # Читаем и проверяем содержимое
    import json
    with open(result_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Проверяем структуру
    assert "metadata" in data, "Нет метаданных в JSON"
    assert "structure" in data, "Нет структуры документа"
    assert "statistics" in data, "Нет статистики в JSON"

    print(f"✅ Размер файла: {Path(result_path).stat().st_size / 1024:.1f} KB")
    print(f"✅ Структура JSON: корректна")
    print(f"✅ Метаданные: {data['metadata']['doc_type']} N {data['metadata']['number']}")
    print(f"✅ Статистика: {data['statistics']['chapters']} глав, {data['statistics']['articles']} статей")

    print("\n✅ JSONExporter работает корректно!\n")
    return result_path


def main():
    """Запуск всех тестов"""
    print("\n")
    print("🚀 Тестирование компонентов K_plus_parcer")
    print("Без необходимости реального PDF файла\n")

    try:
        # Тест 1: Метаданные
        metadata = test_metadata_extractor()

        # Тест 2: Парсинг статей
        chapters, articles = test_article_parser()

        # Тест 3: Markdown экспорт (ПРИОРИТЕТ #1)
        markdown_path = test_markdown_export(metadata, chapters, articles)

        # Тест 4: JSON экспорт
        json_path = test_json_export(metadata, chapters, articles)

        # Итоговый отчёт
        print("=" * 80)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 80)
        print("\n📋 Результаты:")
        print(f"   ✅ MetadataExtractor - работает")
        print(f"   ✅ ArticleParser - работает")
        print(f"   ✅ MarkdownExporter - работает (ПРИОРИТЕТ #1)")
        print(f"   ✅ JSONExporter - работает")
        print("\n📁 Созданные файлы:")
        print(f"   - {markdown_path}")
        print(f"   - {json_path}")
        print("\n🎯 Компоненты готовы для работы с реальными PDF!")
        print("=" * 80)
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ Тест не пройден: {e}")
        logger.exception("Ошибка в тесте")
        return False

    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        logger.exception("Непредвиденная ошибка")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
