#!/usr/bin/env python3
"""
Скрипт проверки готовности системы для запуска пайплайна

Проверяет:
- Версию Python
- Установленные зависимости
- Наличие необходимых директорий
- Наличие PDF файлов для обработки
- Права доступа

Использование:
    python check_setup.py
"""

import sys
import platform
from pathlib import Path
from importlib import import_module


def print_header(text: str):
    """Печать заголовка секции"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_python_version():
    """Проверка версии Python"""
    print_header("🐍 Проверка Python")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"Версия Python: {version_str}")
    print(f"Исполняемый файл: {sys.executable}")
    print(f"Платформа: {platform.platform()}")

    if version.major >= 3 and version.minor >= 8:
        print("✅ Версия Python подходит (>= 3.8)")
        return True
    else:
        print("❌ Требуется Python 3.8 или выше!")
        return False


def check_dependencies():
    """Проверка установленных зависимостей"""
    print_header("📦 Проверка зависимостей")

    required_packages = {
        "pymupdf": "PyMuPDF",
        "pymupdf4llm": "pymupdf4llm",
        "pydantic": "Pydantic",
        "yaml": "PyYAML",
        "loguru": "Loguru",
    }

    all_ok = True

    for module_name, display_name in required_packages.items():
        try:
            import_module(module_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} НЕ УСТАНОВЛЕН")
            all_ok = False

    if not all_ok:
        print("\n⚠️  Установите зависимости:")
        print("   pip install -e .")

    return all_ok


def check_directories():
    """Проверка структуры директорий"""
    print_header("📁 Проверка директорий")

    project_root = Path(__file__).parent

    required_dirs = {
        "src": "Исходный код",
        "data/input/codex": "Входные PDF (кодексы)",
        "data/output": "Выходные данные",
        "examples": "Примеры",
        "logs": "Логи"
    }

    all_ok = True
    missing_dirs = []

    for dir_path, description in required_dirs.items():
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path:25} - {description}")
        else:
            print(f"❌ {dir_path:25} - {description} (НЕ СУЩЕСТВУЕТ)")
            all_ok = False
            missing_dirs.append(dir_path)

    if not all_ok:
        print("\n⚠️  Создайте отсутствующие директории:")
        for dir_path in missing_dirs:
            print(f"   mkdir -p {dir_path}")

    return all_ok


def check_pdf_files():
    """Проверка наличия PDF файлов"""
    print_header("📄 Проверка PDF файлов")

    project_root = Path(__file__).parent
    input_dir = project_root / "data" / "input" / "codex"

    if not input_dir.exists():
        print(f"❌ Директория не существует: {input_dir}")
        print("\n⚠️  Создайте директорию:")
        print(f"   mkdir -p {input_dir}")
        return False

    pdf_files = list(input_dir.glob("*.pdf"))

    if pdf_files:
        print(f"✅ Найдено PDF файлов: {len(pdf_files)}")
        print("\nСписок файлов:")
        for i, pdf_file in enumerate(pdf_files[:10], 1):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            print(f"   {i}. {pdf_file.name} ({size_mb:.1f} MB)")

        if len(pdf_files) > 10:
            print(f"   ... и ещё {len(pdf_files) - 10} файлов")

        return True
    else:
        print(f"❌ PDF файлы не найдены в: {input_dir}")
        print("\n⚠️  Поместите PDF файлы кодексов в:")
        print(f"   {input_dir}")
        return False


def check_write_permissions():
    """Проверка прав на запись"""
    print_header("🔐 Проверка прав доступа")

    project_root = Path(__file__).parent
    test_file = project_root / "data" / "output" / ".test_write"

    try:
        # Создаём директорию если не существует
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Пробуем создать файл
        test_file.write_text("test")
        test_file.unlink()

        print("✅ Права на запись в data/output/ есть")
        return True

    except Exception as e:
        print(f"❌ Нет прав на запись: {e}")
        return False


def check_parser_import():
    """Проверка импорта парсера"""
    print_header("🔧 Проверка парсера")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src import NPAParser

        print("✅ NPAParser импортируется")

        # Пробуем создать экземпляр
        parser = NPAParser()
        print("✅ NPAParser инициализируется")

        return True

    except Exception as e:
        print(f"❌ Ошибка импорта парсера: {e}")
        print("\n⚠️  Установите проект:")
        print("   pip install -e .")
        return False


def print_summary(results: dict):
    """Вывод итоговой сводки"""
    print_header("📊 ИТОГОВАЯ СВОДКА")

    all_ok = all(results.values())

    for check_name, status in results.items():
        status_str = "✅" if status else "❌"
        print(f"{status_str} {check_name}")

    print("\n" + "=" * 70)

    if all_ok:
        print("🎉 ВСЁ ГОТОВО! Можно запускать пайплайн:")
        print("   python pipeline_codex.py")
    else:
        print("⚠️  Обнаружены проблемы. Исправьте их перед запуском.")
        print("   См. подробности выше.")

    print("=" * 70 + "\n")

    return all_ok


def main():
    """Главная функция"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "ПРОВЕРКА ГОТОВНОСТИ СИСТЕМЫ" + " " * 25 + "║")
    print("║" + " " * 18 + "K_plus_parcer Pipeline" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    # Выполнение всех проверок
    results = {
        "Python версия": check_python_version(),
        "Зависимости": check_dependencies(),
        "Структура директорий": check_directories(),
        "PDF файлы": check_pdf_files(),
        "Права доступа": check_write_permissions(),
        "Парсер": check_parser_import()
    }

    # Итоговая сводка
    all_ok = print_summary(results)

    # Дополнительные рекомендации
    if all_ok:
        print("💡 РЕКОМЕНДАЦИИ:")
        print("   1. Сначала протестируйте на одном файле:")
        print("      python pipeline_codex.py --input data/input/test")
        print()
        print("   2. Затем запустите полную обработку:")
        print("      python pipeline_codex.py")
        print()
        print("   3. Результаты будут в:")
        print("      data/output/markdown/  - для RAG систем")
        print("      data/output/json/      - для ML обучения")
        print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
