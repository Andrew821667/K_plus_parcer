"""
Модуль для автоматизации скачивания документов с онлайн КонсультантПлюс

Компоненты:
- ConsultantScraperV2 - основной класс (httpx-based, быстрый)
- ConsultantScraper - старая версия (Selenium, требует отдельной установки)
- Rate Limiter - защита от блокировок
- Авторизация на сайте
- Поиск документов
- Скачивание PDF
"""

from .consultant_scraper_v2 import ConsultantScraperV2
from .rate_limiter import get_rate_limiter, TokenBucketRateLimiter

# Старая версия с Selenium (опционально, требует: pip install selenium webdriver-manager)
# from .consultant_scraper import ConsultantScraper

__all__ = ['ConsultantScraperV2', 'get_rate_limiter', 'TokenBucketRateLimiter']
