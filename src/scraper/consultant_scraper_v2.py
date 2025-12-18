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
    LOGIN_URL = "https://login.consultant.ru/"  # Отдельный поддомен для авторизации

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
        Авторизация на login.consultant.ru

        ⚠️ ТРЕБУЕТСЯ АДАПТАЦИЯ ПОД РЕАЛЬНУЮ СТРУКТУРУ ФОРМЫ ⚠️

        Для адаптации выполните следующие шаги:
        1. Откройте https://login.consultant.ru/ в браузере
        2. Нажмите F12 → вкладка Elements
        3. Найдите форму авторизации (Ctrl+F, поиск '<form')
        4. Изучите имена полей ввода (атрибут 'name' в <input>)
        5. Обновите TODO секции ниже реальными значениями

        Args:
            username: Логин (email)
            password: Пароль

        Returns:
            bool: True если авторизация успешна
        """
        logger.info("Начало авторизации на login.consultant.ru")

        try:
            # ═════════════════════════════════════════════════════════════
            # ШАГ 1: Получаем страницу входа
            # ═════════════════════════════════════════════════════════════
            logger.info(f"Запрос страницы авторизации: {self.LOGIN_URL}")
            response = await self._request_with_retry("GET", self.LOGIN_URL)

            # Парсим HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # ═════════════════════════════════════════════════════════════
            # TODO #1: CSRF ТОКЕН (если используется)
            # ═════════════════════════════════════════════════════════════
            # Найдите в форме скрытое поле с токеном:
            # <input type="hidden" name="???" value="...">
            #
            # Возможные имена: csrf_token, _csrf, token, authenticity_token
            # ─────────────────────────────────────────────────────────────
            csrf_token = soup.find("input", {"type": "hidden", "name": "_csrf"})  # ← ОБНОВИТЕ имя!

            if csrf_token:
                csrf_value = csrf_token.get("value")
                logger.info(f"CSRF токен найден: {csrf_token.get('name')}")
            else:
                csrf_value = None
                logger.info("CSRF токен не обнаружен")

            # ═════════════════════════════════════════════════════════════
            # TODO #2: ФОРМА АВТОРИЗАЦИИ - ИМЕНА ПОЛЕЙ
            # ═════════════════════════════════════════════════════════════
            # Найдите в HTML:
            # <input type="text" name="???" ...>      ← поле логина
            # <input type="password" name="???" ...>  ← поле пароля
            #
            # Типичные варианты:
            # - login, username, email, user, loginname
            # - password, pass, pwd
            # ─────────────────────────────────────────────────────────────
            login_data = {
                "login": username,     # ← ОБНОВИТЕ имя поля логина!
                "password": password,  # ← ОБНОВИТЕ имя поля пароля!
            }

            if csrf_value:
                login_data["_csrf"] = csrf_value  # ← ОБНОВИТЕ имя CSRF поля!

            # ═════════════════════════════════════════════════════════════
            # TODO #3: URL ОТПРАВКИ ФОРМЫ
            # ═════════════════════════════════════════════════════════════
            # Найдите атрибут action формы:
            # <form action="???" method="post">
            #
            # Если action пустой или относительный - используется текущий URL
            # ─────────────────────────────────────────────────────────────
            form = soup.find("form")
            if form and form.get("action"):
                form_action = form.get("action")
                # Если относительный URL - добавляем базовый
                if form_action.startswith("/"):
                    post_url = "https://login.consultant.ru" + form_action
                elif form_action.startswith("http"):
                    post_url = form_action
                else:
                    post_url = self.LOGIN_URL + form_action
            else:
                post_url = self.LOGIN_URL  # Если action пустой

            logger.info(f"POST URL: {post_url}")
            logger.info(f"Данные формы: {list(login_data.keys())}")

            # ═════════════════════════════════════════════════════════════
            # ШАГ 2: Отправляем форму авторизации
            # ═════════════════════════════════════════════════════════════
            response = await self._request_with_retry(
                "POST",
                post_url,
                data=login_data,
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": self.LOGIN_URL
                }
            )

            # ═════════════════════════════════════════════════════════════
            # TODO #4: ПРОВЕРКА УСПЕШНОСТИ АВТОРИЗАЦИИ
            # ═════════════════════════════════════════════════════════════
            # Варианты проверки:
            # 1. Редирект на другую страницу (response.url изменился)
            # 2. Наличие определенных cookie (session_id, auth_token и т.п.)
            # 3. Отсутствие формы авторизации в ответе
            # 4. Наличие специфического текста ("Личный кабинет", имя пользователя)
            # ─────────────────────────────────────────────────────────────

            # Проверка #1: URL изменился (редирект)
            if str(response.url) != post_url and "login" not in str(response.url).lower():
                logger.success(f"✅ Авторизация успешна (редирект на {response.url})")
                return True

            # Проверка #2: Cookie установлены
            if self.session.cookies:
                logger.info(f"Получены cookies: {list(self.session.cookies.keys())}")
                # TODO: Проверьте есть ли специфичные cookie авторизации
                # Например: if 'session_id' in self.session.cookies or 'auth_token' in self.session.cookies

            # Проверка #3: Форма авторизации исчезла
            soup_result = BeautifulSoup(response.text, 'lxml')
            login_form_exists = soup_result.find("form", attrs={"action": lambda x: x and "login" in x.lower()})

            if not login_form_exists:
                logger.success("✅ Авторизация успешна (форма входа отсутствует)")
                return True
            else:
                logger.error("❌ Авторизация не удалась (форма входа всё ещё присутствует)")
                logger.debug(f"Response URL: {response.url}")
                logger.debug(f"Response status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка при авторизации: {e}")
            logger.exception("Детали ошибки:")
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
