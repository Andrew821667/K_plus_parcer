#!/usr/bin/env python3
"""
ПОЛНЫЙ ПАЙПЛАЙН для обработки кодексов РФ (Async версия)

Этапы:
1. Авторизация на онлайн.consultant.ru (httpx + curl-cffi)
2. Поиск документов (все кодексы РФ)
3. Скачивание PDF файлов
4. Парсинг скачанных PDF
5. Экспорт в Markdown (ПРИОРИТЕТ #1 для RAG) и JSON

Использование:
    # С учётными данными из переменных окружения
    export CONSULTANT_USERNAME="your_email@example.com"
    export CONSULTANT_PASSWORD="your_password"
    python pipeline_full.py

    # Или с параметрами командной строки
    python pipeline_full.py --username your_email --password your_pass
"""

import sys
import argparse
import os
import asyncio
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import json

# Импорт компонентов
sys.path.insert(0, str(Path(__file__).parent))
from src.scraper import ConsultantScraperV2
from src import NPAParser
from src.utils.logger import logger


class FullPipelineAsync:
    """
    Полный асинхронный пайплайн: Скачивание → Парсинг → Экспорт

    Объединяет:
    1. ConsultantScraperV2 - httpx-based скачивание PDF (10-20x быстрее Selenium)
    2. NPAParser - парсинг документов
    3. Экспорт в Markdown и JSON

    Преимущества async версии:
    - Параллельное скачивание документов
    - Эффективное использование ресурсов
    - Rate limiting без блокировок
    """

    def __init__(
        self,
        username: str,
        password: str,
        download_dir: str = "data/input/codex",
        output_dir: str = "data/output"
    ):
        """
        Инициализация пайплайна

        Args:
            username: Логин на КонсультантПлюс
            password: Пароль
            download_dir: Директория для скачивания PDF
            output_dir: Директория для результатов парсинга
        """
        self.username = username
        self.password = password
        self.download_dir = Path(download_dir)
        self.output_dir = Path(output_dir)

        # Создаём директории
        self.download_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "markdown").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "json").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)

        # Парсер (синхронный, используется после скачивания)
        self.parser = NPAParser(use_markdown_mode=True, clean_text=True)

        # Статистика
        self.stats = {
            "start_time": None,
            "end_time": None,
            "downloaded": 0,
            "parsed": 0,
            "failed": 0,
            "documents": []
        }

        logger.info("FullPipelineAsync инициализирован")

    async def run(self) -> Dict:
        """
        Запуск полного асинхронного пайплайна

        Returns:
            Dict: Финальная статистика
        """
        print("=" * 80)
        print("🚀 ПОЛНЫЙ АСИНХРОННЫЙ ПАЙПЛАЙН ОБРАБОТКИ КОДЕКСОВ РФ")
        print("=" * 80)
        print("Этапы:")
        print("  1. Авторизация на онлайн.consultant.ru (httpx + rate limiting)")
        print("  2. Поиск и скачивание всех кодексов РФ")
        print("  3. Парсинг скачанных PDF")
        print("  4. Экспорт в Markdown (RAG) и JSON (ML)")
        print("=" * 80)
        print()

        self.stats["start_time"] = datetime.now()

        try:
            # ЭТАП 1 + 2: Авторизация и скачивание (async)
            print("📥 ЭТАП 1-2: Авторизация и скачивание кодексов...")

            async with ConsultantScraperV2(
                download_dir=str(self.download_dir),
                rate_limit=0.5,  # 0.5 req/sec = 1 запрос каждые 2 сек
                max_retries=3
            ) as scraper:
                # Авторизация
                print("   🔐 Авторизация на сайте...")
                if not await scraper.login(self.username, self.password):
                    print("   ❌ Ошибка авторизации!")
                    return self.stats

                print("   ✅ Авторизация успешна")

                # Скачивание кодексов
                print("   📥 Поиск и скачивание кодексов...")
                downloaded_files = await scraper.search_and_download_codex()

                if not downloaded_files:
                    print("   ❌ Не удалось скачать документы!")
                    return self.stats

                self.stats["downloaded"] = len(downloaded_files)
                print(f"   ✅ Скачано файлов: {len(downloaded_files)}\n")

            # ЭТАП 3: Парсинг документов (синхронный)
            print("🔧 ЭТАП 3: Парсинг скачанных PDF...")
            self._parse_documents(downloaded_files)

            # ЭТАП 4: Генерация отчёта
            self.stats["end_time"] = datetime.now()
            self._generate_report()

            # Итоговая статистика
            self._print_summary()

            return self.stats

        except KeyboardInterrupt:
            print("\n\n⚠️  Обработка прервана пользователем")
            return self.stats

        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
            logger.exception("Критическая ошибка в пайплайне")
            return self.stats

    def _parse_documents(self, pdf_files: List[str]):
        """
        Парсинг списка PDF файлов

        Args:
            pdf_files: Список путей к PDF файлам
        """
        total = len(pdf_files)

        for i, pdf_path in enumerate(pdf_files, 1):
            filename = Path(pdf_path).name
            print(f"[{i}/{total}] Обработка: {filename}")

            doc_stats = {
                "filename": filename,
                "status": "unknown",
                "error": None,
                "doc_type": None,
                "number": None,
                "chapters": 0,
                "articles": 0
            }

            try:
                # Парсинг
                document = self.parser.parse(pdf_path)

                # Экспорт
                output_name = Path(pdf_path).stem

                # Markdown (ПРИОРИТЕТ #1)
                markdown_path = self.output_dir / "markdown" / f"{output_name}.md"
                document.export_markdown(str(markdown_path))

                # JSON
                json_path = self.output_dir / "json" / f"{output_name}.json"
                document.export_json(str(json_path))

                # Статистика
                doc_stats.update({
                    "status": "success",
                    "doc_type": document.metadata.doc_type,
                    "number": document.metadata.number,
                    "chapters": len(document.chapters),
                    "articles": len(document.articles) if document.articles else sum(
                        len(ch.articles) for ch in document.chapters
                    )
                })

                self.stats["parsed"] += 1
                print(f"   ✅ {doc_stats['doc_type']} N {doc_stats['number']}, "
                      f"{doc_stats['chapters']} глав, {doc_stats['articles']} статей\n")

            except Exception as e:
                doc_stats["status"] = "failed"
                doc_stats["error"] = str(e)
                self.stats["failed"] += 1
                print(f"   ❌ Ошибка: {e}\n")
                logger.error(f"Ошибка при парсинге {filename}: {e}")

            self.stats["documents"].append(doc_stats)

    def _generate_report(self):
        """Генерация отчёта о работе пайплайна"""
        report_path = self.output_dir / "reports" / f"full_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

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
        print("📊 ИТОГОВАЯ СТАТИСТИКА ПОЛНОГО ПАЙПЛАЙНА")
        print("=" * 80)
        print(f"Скачано PDF:         {self.stats['downloaded']} ✅")
        print(f"Распарсено успешно:  {self.stats['parsed']} ✅")
        print(f"Ошибок:              {self.stats['failed']} ❌")
        print(f"Время работы:        {total_time:.1f}s ({total_time/60:.1f} мин)")
        print()
        print("📁 Результаты:")
        print(f"   Markdown (RAG):  {self.output_dir / 'markdown'}")
        print(f"   JSON (ML):       {self.output_dir / 'json'}")
        print(f"   Отчёты:          {self.output_dir / 'reports'}")
        print()

        if self.stats["parsed"] > 0:
            print("📚 Обработанные документы:")
            for doc in self.stats["documents"]:
                if doc["status"] == "success":
                    print(f"   ✅ {doc['filename']}: {doc['doc_type']} N {doc['number']}, "
                          f"{doc['articles']} статей")

        if self.stats["failed"] > 0:
            print()
            print("❌ Ошибки:")
            for doc in self.stats["documents"]:
                if doc["status"] == "failed":
                    print(f"   • {doc['filename']}: {doc['error']}")

        print("=" * 80)


async def main_async():
    """Асинхронная точка входа в полный пайплайн"""
    parser = argparse.ArgumentParser(
        description="Полный асинхронный пайплайн обработки кодексов РФ: Скачивание + Парсинг + Экспорт",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # С учётными данными из переменных окружения
  export CONSULTANT_USERNAME="your_email@example.com"
  export CONSULTANT_PASSWORD="your_password"
  python pipeline_full.py

  # С параметрами командной строки
  python pipeline_full.py --username your_email --password your_pass

  # С кастомными директориями
  python pipeline_full.py --download-dir data/downloads --output-dir data/results

⚠️  ВАЖНО:
  - Требуется активная подписка на онлайн.consultant.ru
  - Используется httpx + curl-cffi (БЕЗ браузера, быстрее Selenium в 10-20 раз)
  - Rate limiting: 0.5 req/sec (защита от блокировок)

Результаты:
  data/output/markdown/ - Markdown база для RAG систем
  data/output/json/     - JSON данные для ML обучения
  data/output/reports/  - Отчёты о работе пайплайна
        """
    )

    parser.add_argument(
        "--username",
        type=str,
        help="Логин на КонсультантПлюс (или через CONSULTANT_USERNAME)"
    )

    parser.add_argument(
        "--password",
        type=str,
        help="Пароль (или через CONSULTANT_PASSWORD)"
    )

    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("data/input/codex"),
        help="Директория для скачивания PDF (default: data/input/codex)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
        help="Директория для результатов (default: data/output)"
    )

    args = parser.parse_args()

    # Получение учётных данных
    username = args.username or os.getenv("CONSULTANT_USERNAME")
    password = args.password or os.getenv("CONSULTANT_PASSWORD")

    if not username or not password:
        print("❌ Ошибка: Не указаны учётные данные!")
        print()
        print("Используйте один из вариантов:")
        print("  1. Параметры: --username USER --password PASS")
        print("  2. Переменные окружения:")
        print("     export CONSULTANT_USERNAME='your_email'")
        print("     export CONSULTANT_PASSWORD='your_password'")
        print()
        sys.exit(1)

    # Создание и запуск пайплайна
    pipeline = FullPipelineAsync(
        username=username,
        password=password,
        download_dir=str(args.download_dir),
        output_dir=str(args.output_dir)
    )

    try:
        stats = await pipeline.run()

        # Код выхода
        exit_code = 0 if stats["failed"] == 0 else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.exception("Критическая ошибка")
        sys.exit(1)


def main():
    """Синхронная обертка для запуска async main"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
