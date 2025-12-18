"""
Scraper для автоматизации скачивания документов с онлайн.consultant.ru

Использует Selenium для:
1. Открытия браузера
2. Авторизации на сайте
3. Поиска документов (кодексы, законы и т.д.)
4. Скачивания PDF файлов
"""

import time
import os
from pathlib import Path
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import logger


class ConsultantScraper:
    """
    Автоматизация работы с онлайн КонсультантПлюс

    Основные функции:
    - Авторизация на сайте
    - Поиск документов по критериям
    - Скачивание PDF файлов
    """

    # URLs
    BASE_URL = "https://online.consultant.ru"
    LOGIN_URL = f"{BASE_URL}/auth/login"
    SEARCH_URL = f"{BASE_URL}/cgi/online.cgi?req=doc"

    def __init__(
        self,
        download_dir: str,
        headless: bool = False,
        wait_timeout: int = 20
    ):
        """
        Инициализация scraper

        Args:
            download_dir: Директория для скачивания PDF
            headless: Запуск браузера в headless режиме (без GUI)
            wait_timeout: Таймаут ожидания элементов (секунды)
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.wait = None

        logger.info(f"ConsultantScraper инициализирован: {download_dir}")

    def _setup_driver(self):
        """Настройка Chrome WebDriver"""
        chrome_options = Options()

        # Headless режим
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")

        # Настройки скачивания
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # Скачивать PDF, а не открывать
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Дополнительные опции
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # User agent
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)

        logger.info("Chrome WebDriver настроен и запущен")

    def start(self):
        """Запуск браузера"""
        if not self.driver:
            self._setup_driver()

        self.driver.get(self.BASE_URL)
        logger.info(f"Открыта главная страница: {self.BASE_URL}")
        time.sleep(2)

    def login(self, username: str, password: str):
        """
        Авторизация на сайте

        Args:
            username: Логин (email/телефон)
            password: Пароль

        Returns:
            bool: True если авторизация успешна
        """
        logger.info("Начало авторизации на сайте")

        try:
            # Переход на страницу входа
            self.driver.get(self.LOGIN_URL)
            time.sleep(2)

            # Поиск полей логина и пароля
            # ВНИМАНИЕ: Селекторы могут измениться! Нужно проверить актуальные
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
                # Альтернативные селекторы:
                # By.NAME, "login"
                # By.CSS_SELECTOR, "input[type='email']"
            )

            password_field = self.driver.find_element(By.ID, "password")
            # Альтернатива: By.CSS_SELECTOR, "input[type='password']"

            # Ввод данных
            username_field.clear()
            username_field.send_keys(username)

            password_field.clear()
            password_field.send_keys(password)

            logger.info("Учётные данные введены")

            # Поиск и клик по кнопке входа
            login_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
                # Альтернативы:
                # By.XPATH, "//button[contains(text(), 'Войти')]"
            )
            login_button.click()

            # Ожидание успешной авторизации
            # Проверяем появление элемента профиля или исчезновение формы входа
            time.sleep(3)

            # Проверка успешности
            if "login" not in self.driver.current_url.lower():
                logger.success("✅ Авторизация успешна")
                return True
            else:
                logger.error("❌ Авторизация не удалась")
                return False

        except TimeoutException:
            logger.error("❌ Таймаут при авторизации: элементы не найдены")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при авторизации: {e}")
            return False

    def search_documents(self, query: str, doc_type: Optional[str] = None) -> List[Dict]:
        """
        Поиск документов на сайте

        Args:
            query: Поисковый запрос (например, "Гражданский кодекс")
            doc_type: Тип документа (например, "Кодексы")

        Returns:
            List[Dict]: Список найденных документов с метаданными
        """
        logger.info(f"Поиск документов: '{query}'")

        try:
            # Переход на страницу поиска
            self.driver.get(self.SEARCH_URL)
            time.sleep(2)

            # Поиск поля ввода
            search_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "search-query"))
                # Альтернативы:
                # By.NAME, "query"
                # By.CSS_SELECTOR, "input[type='search']"
            )

            search_field.clear()
            search_field.send_keys(query)

            # Выбор типа документа (если указан)
            if doc_type:
                # ВНИМАНИЕ: Реализация зависит от структуры сайта
                logger.info(f"Фильтр по типу документа: {doc_type}")
                # Пример: выбор из dropdown
                # doc_type_dropdown = self.driver.find_element(By.ID, "doc-type-filter")
                # ...

            # Клик по кнопке поиска
            search_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            search_button.click()

            # Ожидание результатов
            time.sleep(3)

            # Парсинг результатов поиска
            documents = self._parse_search_results()

            logger.info(f"Найдено документов: {len(documents)}")
            return documents

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске документов: {e}")
            return []

    def _parse_search_results(self) -> List[Dict]:
        """
        Парсинг результатов поиска

        Returns:
            List[Dict]: Список документов с метаданными
        """
        documents = []

        try:
            # Поиск элементов результатов
            # ВНИМАНИЕ: Селекторы зависят от структуры сайта!
            result_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".search-result-item"
                # Альтернативы нужно определить по структуре HTML
            )

            for element in result_elements:
                try:
                    # Извлечение данных о документе
                    title = element.find_element(By.CSS_SELECTOR, ".doc-title").text
                    link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                    # Дополнительные метаданные (если доступны)
                    doc_info = {
                        "title": title,
                        "url": link,
                        "element": element  # Сохраняем для последующего взаимодействия
                    }

                    documents.append(doc_info)

                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.error(f"Ошибка при парсинге результатов: {e}")

        return documents

    def download_document_pdf(self, doc_url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Скачивание PDF документа

        Args:
            doc_url: URL документа
            filename: Имя файла для сохранения (опционально)

        Returns:
            str: Путь к скачанному файлу или None при ошибке
        """
        logger.info(f"Скачивание PDF: {doc_url}")

        try:
            # Переход на страницу документа
            self.driver.get(doc_url)
            time.sleep(3)

            # Поиск кнопки "Скачать PDF" или аналогичной
            # ВНИМАНИЕ: Селекторы нужно адаптировать под реальный сайт!
            pdf_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//a[contains(text(), 'PDF')] | //button[contains(text(), 'PDF')]"
                ))
            )

            # Клик по кнопке скачивания
            pdf_button.click()

            # Ожидание завершения скачивания
            downloaded_file = self._wait_for_download(timeout=30)

            if downloaded_file:
                # Переименование если указано имя
                if filename:
                    new_path = self.download_dir / filename
                    os.rename(downloaded_file, new_path)
                    downloaded_file = new_path

                logger.success(f"✅ PDF скачан: {downloaded_file}")
                return str(downloaded_file)
            else:
                logger.error("❌ Не удалось скачать PDF")
                return None

        except TimeoutException:
            logger.error("❌ Таймаут: кнопка скачивания не найдена")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при скачивании PDF: {e}")
            return None

    def _wait_for_download(self, timeout: int = 30) -> Optional[Path]:
        """
        Ожидание завершения скачивания файла

        Args:
            timeout: Максимальное время ожидания (секунды)

        Returns:
            Path: Путь к скачанному файлу или None
        """
        # Получаем список файлов до скачивания
        files_before = set(self.download_dir.glob("*"))

        # Ожидаем появления нового файла
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(1)

            # Проверяем новые файлы
            files_after = set(self.download_dir.glob("*"))
            new_files = files_after - files_before

            # Проверяем что нет временных файлов (.crdownload, .tmp)
            complete_files = [
                f for f in new_files
                if not f.name.endswith(('.crdownload', '.tmp', '.part'))
            ]

            if complete_files:
                return complete_files[0]

        return None

    def search_and_download_codex(self, save_dir: Optional[str] = None) -> List[str]:
        """
        Поиск и скачивание всех кодексов РФ

        Args:
            save_dir: Директория для сохранения (по умолчанию download_dir)

        Returns:
            List[str]: Список путей к скачанным файлам
        """
        logger.info("Поиск и скачивание всех кодексов РФ")

        # Список кодексов для скачивания
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
                # Поиск кодекса
                documents = self.search_documents(codex_name, doc_type="Кодексы")

                if not documents:
                    logger.warning(f"⚠️  {codex_name} не найден")
                    continue

                # Берём первый результат (обычно самый релевантный)
                doc = documents[0]

                # Формируем имя файла
                filename = f"{codex_name.replace(' ', '_')}.pdf"

                # Скачиваем
                pdf_path = self.download_document_pdf(doc['url'], filename)

                if pdf_path:
                    downloaded_files.append(pdf_path)

                # Задержка между запросами
                time.sleep(2)

            except Exception as e:
                logger.error(f"Ошибка при обработке {codex_name}: {e}")
                continue

        logger.success(f"✅ Скачано кодексов: {len(downloaded_files)}/{len(codex_list)}")
        return downloaded_files

    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("Браузер закрыт")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Вспомогательные функции

def get_credentials_from_env() -> tuple:
    """
    Получение учётных данных из переменных окружения

    Returns:
        tuple: (username, password)
    """
    username = os.getenv("CONSULTANT_USERNAME")
    password = os.getenv("CONSULTANT_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Учётные данные не найдены! Установите переменные окружения:\n"
            "CONSULTANT_USERNAME и CONSULTANT_PASSWORD"
        )

    return username, password
