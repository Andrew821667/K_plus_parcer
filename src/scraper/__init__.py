"""
Модуль для автоматизации скачивания документов с онлайн КонсультантПлюс

Компоненты:
- ConsultantScraper - основной класс для работы с сайтом
- Авторизация на сайте
- Поиск документов
- Скачивание PDF
"""

from .consultant_scraper import ConsultantScraper

__all__ = ['ConsultantScraper']
