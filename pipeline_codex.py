#!/usr/bin/env python3
"""
Пайплайн для массовой обработки кодексов РФ

Обрабатывает все PDF файлы кодексов из входной директории,
создаёт Markdown базу знаний и JSON файлы для ML/RAG систем.

Использование:
    python pipeline_codex.py --input data/input/codex --output data/output

Требования:
    - PDF файлы кодексов в директории input/
    - Установленные зависимости (pip install -e .)
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json
import time

# Импорт парсера
sys.path.insert(0, str(Path(__file__).parent))
from src import NPAParser
from src.utils.logger import logger


class CodexPipeline:
    """
    Пайплайн для массовой обработки кодексов РФ

    Особенности:
    - Batch обработка всех PDF из директории
    - Подробное логирование процесса
    - Сбор статистики по каждому документу
    - Обработка ошибок с продолжением работы
    - Генерация итогового отчёта
    """

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        use_markdown_mode: bool = True,
        clean_text: bool = True
    ):
        """
        Инициализация пайплайна

        Args:
            input_dir: Директория с PDF файлами кодексов
            output_dir: Директория для результатов
            use_markdown_mode: Использовать pymupdf4llm для Markdown
            clean_text: Очищать текст от артефактов
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.use_markdown_mode = use_markdown_mode
        self.clean_text = clean_text

        # Создаём выходные директории
        self.markdown_dir = self.output_dir / "markdown"
        self.json_dir = self.output_dir / "json"
        self.reports_dir = self.output_dir / "reports"

        for dir_path in [self.markdown_dir, self.json_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Инициализация парсера
        self.parser = NPAParser(
            use_markdown_mode=use_markdown_mode,
            clean_text=clean_text
        )

        # Статистика обработки
        self.stats = {
            "total_files": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
            "documents": []
        }

        logger.info(f"Пайплайн инициализирован: {input_dir} -> {output_dir}")

    def find_pdf_files(self) -> List[Path]:
        """
        Поиск всех PDF файлов во входной директории

        Returns:
            List[Path]: Список путей к PDF файлам
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))
        pdf_files.extend(self.input_dir.glob("**/*.pdf"))

        # Удаляем дубликаты
        pdf_files = list(set(pdf_files))
        pdf_files.sort()

        logger.info(f"Найдено PDF файлов: {len(pdf_files)}")
        return pdf_files

    def process_document(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Обработка одного документа

        Args:
            pdf_path: Путь к PDF файлу

        Returns:
            Dict: Статистика обработки документа
        """
        doc_stats = {
            "filename": pdf_path.name,
            "status": "unknown",
            "error": None,
            "doc_type": None,
            "number": None,
            "chapters": 0,
            "articles": 0,
            "processing_time": 0,
            "markdown_size": 0,
            "json_size": 0
        }

        start_time = time.time()

        try:
            logger.info(f"Обработка: {pdf_path.name}")

            # Парсинг документа
            document = self.parser.parse(str(pdf_path))

            # Формируем имя выходных файлов
            output_name = pdf_path.stem

            # Экспорт в Markdown (ПРИОРИТЕТ #1)
            markdown_path = self.markdown_dir / f"{output_name}.md"
            document.export_markdown(str(markdown_path))

            # Экспорт в JSON
            json_path = self.json_dir / f"{output_name}.json"
            document.export_json(str(json_path))

            # Сбор статистики
            doc_stats.update({
                "status": "success",
                "doc_type": document.metadata.doc_type,
                "number": document.metadata.number,
                "chapters": len(document.chapters),
                "articles": len(document.articles) if document.articles else sum(
                    len(ch.articles) for ch in document.chapters
                ),
                "processing_time": time.time() - start_time,
                "markdown_size": markdown_path.stat().st_size,
                "json_size": json_path.stat().st_size
            })

            logger.success(
                f"✅ {pdf_path.name}: "
                f"{doc_stats['doc_type']} N {doc_stats['number']}, "
                f"{doc_stats['chapters']} глав, {doc_stats['articles']} статей"
            )

        except Exception as e:
            doc_stats["status"] = "failed"
            doc_stats["error"] = str(e)
            doc_stats["processing_time"] = time.time() - start_time

            logger.error(f"❌ Ошибка при обработке {pdf_path.name}: {e}")

        return doc_stats

    def run(self) -> Dict[str, Any]:
        """
        Запуск пайплайна обработки всех документов

        Returns:
            Dict: Финальная статистика обработки
        """
        print("=" * 80)
        print("🚀 ПАЙПЛАЙН ОБРАБОТКИ КОДЕКСОВ РФ")
        print("=" * 80)
        print(f"Входная директория: {self.input_dir}")
        print(f"Выходная директория: {self.output_dir}")
        print(f"Markdown режим: {'Да' if self.use_markdown_mode else 'Нет'}")
        print(f"Очистка текста: {'Да' if self.clean_text else 'Нет'}")
        print("=" * 80)
        print()

        # Поиск PDF файлов
        pdf_files = self.find_pdf_files()

        if not pdf_files:
            logger.warning("⚠️  PDF файлы не найдены!")
            print("\n⚠️  PDF файлы не найдены в директории:")
            print(f"   {self.input_dir}")
            print("\nПоместите PDF файлы кодексов в эту директорию и запустите снова.")
            return self.stats

        self.stats["total_files"] = len(pdf_files)
        self.stats["start_time"] = datetime.now()

        print(f"📚 Найдено документов: {len(pdf_files)}")
        print()

        # Обработка каждого документа
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Обработка: {pdf_path.name}")

            doc_stats = self.process_document(pdf_path)
            self.stats["documents"].append(doc_stats)

            if doc_stats["status"] == "success":
                self.stats["processed"] += 1
                print(f"   ✅ Успешно ({doc_stats['processing_time']:.1f}s)")
            elif doc_stats["status"] == "failed":
                self.stats["failed"] += 1
                print(f"   ❌ Ошибка: {doc_stats['error']}")

            print()

        self.stats["end_time"] = datetime.now()

        # Генерация отчёта
        self._generate_report()

        # Вывод итоговой статистики
        self._print_summary()

        return self.stats

    def _generate_report(self):
        """Генерация детального отчёта о обработке"""
        report_path = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    **self.stats,
                    "start_time": self.stats["start_time"].isoformat(),
                    "end_time": self.stats["end_time"].isoformat(),
                    "total_time": (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
                },
                f,
                ensure_ascii=False,
                indent=2
            )

        logger.info(f"Отчёт сохранён: {report_path}")

    def _print_summary(self):
        """Вывод итоговой статистики"""
        total_time = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        print("=" * 80)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 80)
        print(f"Всего файлов:        {self.stats['total_files']}")
        print(f"Обработано успешно:  {self.stats['processed']} ✅")
        print(f"Ошибок:              {self.stats['failed']} ❌")
        print(f"Время обработки:     {total_time:.1f}s ({total_time/60:.1f} мин)")

        if self.stats["processed"] > 0:
            avg_time = total_time / self.stats["processed"]
            print(f"Среднее время/док:   {avg_time:.1f}s")

        print()
        print("📁 Результаты:")
        print(f"   Markdown: {self.markdown_dir}")
        print(f"   JSON:     {self.json_dir}")
        print(f"   Отчёты:   {self.reports_dir}")
        print()

        # Детали по документам
        if self.stats["processed"] > 0:
            print("📚 Обработанные документы:")
            for doc in self.stats["documents"]:
                if doc["status"] == "success":
                    print(f"   ✅ {doc['filename']}: {doc['articles']} статей, "
                          f"{doc['markdown_size']/1024:.1f} KB (MD)")

        if self.stats["failed"] > 0:
            print()
            print("❌ Ошибки:")
            for doc in self.stats["documents"]:
                if doc["status"] == "failed":
                    print(f"   • {doc['filename']}: {doc['error']}")

        print("=" * 80)


def main():
    """Точка входа в пайплайн"""
    parser = argparse.ArgumentParser(
        description="Пайплайн обработки кодексов РФ для ML/RAG систем",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовое использование
  python pipeline_codex.py

  # Указать входную и выходную директории
  python pipeline_codex.py --input data/input/codex --output data/output

  # Отключить Markdown режим
  python pipeline_codex.py --no-markdown-mode

  # Отключить очистку текста
  python pipeline_codex.py --no-clean-text

Структура директорий:
  data/
    input/
      codex/              <- Сюда поместите PDF файлы кодексов
    output/
      markdown/           <- Markdown база знаний (ПРИОРИТЕТ для RAG)
      json/               <- JSON структурированные данные
      reports/            <- Отчёты о обработке
        """
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/input/codex"),
        help="Директория с PDF файлами кодексов (default: data/input/codex)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output"),
        help="Директория для результатов (default: data/output)"
    )

    parser.add_argument(
        "--no-markdown-mode",
        action="store_true",
        help="Отключить pymupdf4llm (использовать только PyMuPDF)"
    )

    parser.add_argument(
        "--no-clean-text",
        action="store_true",
        help="Отключить очистку текста от артефактов"
    )

    args = parser.parse_args()

    # Создаём и запускаем пайплайн
    pipeline = CodexPipeline(
        input_dir=args.input,
        output_dir=args.output,
        use_markdown_mode=not args.no_markdown_mode,
        clean_text=not args.no_clean_text
    )

    try:
        stats = pipeline.run()

        # Код выхода: 0 если все успешно, 1 если были ошибки
        exit_code = 0 if stats["failed"] == 0 else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n⚠️  Обработка прервана пользователем")
        logger.warning("Обработка прервана пользователем")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        logger.exception("Критическая ошибка в пайплайне")
        sys.exit(1)


if __name__ == "__main__":
    main()
