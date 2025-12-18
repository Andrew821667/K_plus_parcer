"""
Улучшенный scraper для КонсультантПлюс

Использует приемы из kad_parcer:
- httpx вместо Selenium (быстрее и надежнее)
- Token Bucket Rate Limiter (защита от блокировок)
- Retry logic с экспоненциальной задержкой
- curl-cffi для обхода защиты

ВАЖНО: Этот код нужно будет адаптировать под конкретную структуру
сайта онлайн.consultant.ru после изучения его API/форм.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional
from curl_cffi import requests as curl_requests
import httpx
from bs4 import BeautifulSoup

from .rate_limiter import get_rate_limiter
from ..utils.logger import logger


class ConsultantScraperV2:
    """
    Улучшенный scraper для автоматизации работы с КонсультантПлюс

    Преимущества над Selenium:
    - В 10-20 раз быстрее
    - Меньше потребление памяти
    - Не требует браузера
    - Проще обрабатывать ошибки
    - Легче масштабировать
    """

    BASE_URL = "https://online.consultant.ru"

    def __init__(
        self,
        download_dir: str,
        rate_limit: float = 0.5,  # 0.5 запросов/сек = 1 запрос каждые 2 сек
        max_retries: int = 3
    ):
        """
        Инициализация scraper

        Args:
            download_dir: Директория для скачивания PDF
            rate_limit: Ограничение скорости запросов
            max_retries: Максимальное количество повторов при ошибке
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.max_retries = max_retries

        # Rate limiter для защиты от блокировок
        self.rate_limiter = get_rate_limiter(
            rate=rate_limit,
            burst_size=3,
            rate_limit_seconds=2.0
        )

        # HTTP клиент
        self.session = None
        self.cookies = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
        }

        logger.info(f"ConsultantScraperV2 инициализирован: {download_dir}")

    async def __aenter__(self):
        """Async context manager entry"""
        # Создаем HTTP клиент с поддержкой cookie
        self.session = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        HTTP запрос с повторами и rate limiting

        Args:
            method: HTTP метод (GET, POST и т.д.)
            url: URL
            **kwargs: Дополнительные параметры для httpx

        Returns:
            httpx.Response: Ответ сервера

        Raises:
            Exception: После всех неудачных попыток
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Ждем разрешения от rate limiter
                await self.rate_limiter.acquire()

                # Делаем запрос
                response = await self.session.request(method, url, **kwargs)
                response.raise_for_status()

                return response

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                # Если 429 (Too Many Requests) - увеличиваем задержку
                if status_code == 429:
                    wait_time = 2 ** (attempt + 2)  # 4, 8, 16 секунд
                    logger.warning(f"429 Too Many Requests, ждем {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                # Если 5xx - пробуем еще раз
                if 500 <= status_code < 600:
                    wait_time = 2 ** (attempt + 1)  # 2, 4, 8 секунд
                    logger.warning(f"Ошибка сервера {status_code}, повтор через {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                # Другие ошибки - не ретраим
                raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                wait_time = 2 ** attempt  # 1, 2, 4 секунды
                logger.warning(f"Ошибка соединения, повтор {attempt+1}/{self.max_retries} через {wait_time}s")
                await asyncio.sleep(wait_time)

        # Все попытки исчерпаны
        logger.error(f"Все {self.max_retries} попыток исчерпаны для {url}")
        raise last_error

    async def login(self, username: str, password: str) -> bool:
        """
        Авторизация на сайте

        ВАЖНО: Эту функцию нужно адаптировать под реальную структуру
        формы авторизации на онлайн.consultant.ru

        Args:
            username: Логин
            password: Пароль

        Returns:
            bool: True если авторизация успешна
        """
        logger.info("Начало авторизации")

        try:
            # Шаг 1: Получаем страницу входа (для CSRF токена если нужен)
            login_page_url = f"{self.BASE_URL}/auth/login"
            response = await self._request_with_retry("GET", login_page_url)

            # Парсим HTML для поиска CSRF токена (если используется)
            soup = BeautifulSoup(response.text, 'lxml')

            # TODO: Найти реальные имена полей на сайте
            # Пример структуры которую нужно проверить:
            csrf_token = soup.find("input", {"name": "csrf_token"})
            if csrf_token:
                csrf_value = csrf_token.get("value")
                logger.info("CSRF токен найден")
            else:
                csrf_value = None

            # Шаг 2: Отправляем форму авторизации
            login_data = {
                "username": username,  # TODO: Проверить реальное имя поля
                "password": password,  # TODO: Проверить реальное имя поля
            }

            if csrf_value:
                login_data["csrf_token"] = csrf_value

            # POST запрос с данными авторизации
            response = await self._request_with_retry(
                "POST",
                login_page_url,
                data=login_data
            )

            # Проверка успешности авторизации
            # TODO: Проверить как именно сайт отвечает при успешном входе
            if "login" not in response.url.path.lower():
                logger.success("✅ Авторизация успешна")
                return True
            else:
                logger.error("❌ Авторизация не удалась")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка при авторизации: {e}")
            return False

    async def search_documents(
        self,
        query: str,
        doc_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Поиск документов

        ВАЖНО: Адаптировать под реальное API/формы поиска

        Args:
            query: Поисковый запрос
            doc_type: Тип документа (опционально)

        Returns:
            List[Dict]: Список найденных документов
        """
        logger.info(f"Поиск документов: '{query}'")

        try:
            # TODO: Узнать реальную структуру поиска на сайте
            # Может быть API endpoint или форма
            search_url = f"{self.BASE_URL}/cgi/online.cgi"

            params = {
                "req": "doc",
                "query": query
            }

            if doc_type:
                params["doc_type"] = doc_type

            response = await self._request_with_retry(
                "GET",
                search_url,
                params=params
            )

            # Парсинг результатов
            documents = await self._parse_search_results(response.text)

            logger.info(f"Найдено документов: {len(documents)}")
            return documents

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске: {e}")
            return []

    async def _parse_search_results(self, html: str) -> List[Dict]:
        """
        Парсинг результатов поиска из HTML

        TODO: Адаптировать под реальную структуру HTML
        """
        documents = []
        soup = BeautifulSoup(html, 'lxml')

        # TODO: Найти реальные CSS селекторы для результатов
        results = soup.select(".search-result-item")  # Примерный селектор

        for result in results:
            try:
                title_elem = result.select_one(".doc-title")
                link_elem = result.select_one("a[href]")

                if title_elem and link_elem:
                    doc = {
                        "title": title_elem.text.strip(),
                        "url": link_elem["href"]
                    }
                    documents.append(doc)

            except Exception as e:
                logger.warning(f"Ошибка при парсинге результата: {e}")
                continue

        return documents

    async def download_document_pdf(
        self,
        doc_url: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Скачивание PDF документа

        Args:
            doc_url: URL документа
            filename: Имя файла (опционально)

        Returns:
            str: Путь к скачанному файлу или None
        """
        logger.info(f"Скачивание PDF: {doc_url}")

        try:
            # Скачиваем PDF
            response = await self._request_with_retry("GET", doc_url)

            # Определяем имя файла
            if not filename:
                # Пробуем извлечь из Content-Disposition header
                content_disp = response.headers.get("content-disposition", "")
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[1].strip('"')
                else:
                    filename = f"document_{int(time.time())}.pdf"

            # Сохраняем файл
            file_path = self.download_dir / filename
            file_path.write_bytes(response.content)

            logger.success(f"✅ PDF скачан: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"❌ Ошибка при скачивании: {e}")
            return None

    async def search_and_download_codex(self) -> List[str]:
        """
        Поиск и скачивание всех кодексов РФ

        Returns:
            List[str]: Список путей к скачанным файлам
        """
        logger.info("Поиск и скачивание всех кодексов РФ")

        codex_list = [
            "Гражданский кодекс часть 1",
            "Гражданский кодекс часть 2",
            "Гражданский кодекс часть 3",
            "Гражданский кодекс часть 4",
            "Уголовный кодекс",
            "Налоговый кодекс часть 1",
            "Налоговый кодекс часть 2",
            "Трудовой кодекс",
            "Семейный кодекс",
            "Кодекс об административных правонарушениях",
            "Арбитражный процессуальный кодекс",
            "Гражданский процессуальный кодекс",
            "Уголовно-процессуальный кодекс",
            "Земельный кодекс",
            "Жилищный кодекс",
            "Бюджетный кодекс",
            "Градостроительный кодекс",
            "Водный кодекс",
            "Лесной кодекс",
            "Воздушный кодекс",
        ]

        downloaded_files = []

        for codex_name in codex_list:
            logger.info(f"Обработка: {codex_name}")

            try:
                # Поиск
                documents = await self.search_documents(codex_name, doc_type="Кодексы")

                if not documents:
                    logger.warning(f"⚠️  {codex_name} не найден")
                    continue

                # Берём первый результат
                doc = documents[0]
                filename = f"{codex_name.replace(' ', '_')}.pdf"

                # Скачиваем
                pdf_path = await self.download_document_pdf(doc['url'], filename)

                if pdf_path:
                    downloaded_files.append(pdf_path)

            except Exception as e:
                logger.error(f"Ошибка при обработке {codex_name}: {e}")
                continue

        logger.success(f"✅ Скачано кодексов: {len(downloaded_files)}/{len(codex_list)}")
        return downloaded_files
