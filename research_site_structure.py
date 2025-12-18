#!/usr/bin/env python3
"""
Скрипт для исследования структуры онлайн.consultant.ru

Использует curl-cffi для обхода защиты от ботов.
Сохраняет HTML страниц для анализа.
"""

import asyncio
from pathlib import Path
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup


async def fetch_page(url: str, session=None) -> tuple[str, str]:
    """
    Получить страницу с использованием curl-cffi

    Returns:
        (html, error_message)
    """
    try:
        print(f"📡 Запрос: {url}")

        # Используем curl-cffi с имитацией Chrome браузера
        response = curl_requests.get(
            url,
            impersonate="chrome110",  # Имитация Chrome 110
            timeout=10
        )

        print(f"   ✅ Статус: {response.status_code}")

        if response.status_code == 200:
            return response.text, None
        else:
            return None, f"HTTP {response.status_code}"

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None, str(e)


def analyze_login_form(html: str):
    """Анализ формы авторизации"""
    soup = BeautifulSoup(html, 'lxml')

    print("\n🔍 АНАЛИЗ ФОРМЫ АВТОРИЗАЦИИ:")
    print("=" * 60)

    # Ищем все формы
    forms = soup.find_all('form')
    print(f"Найдено форм: {len(forms)}")

    for i, form in enumerate(forms, 1):
        print(f"\nФорма #{i}:")
        print(f"  Action: {form.get('action', 'N/A')}")
        print(f"  Method: {form.get('method', 'N/A')}")
        print(f"  ID: {form.get('id', 'N/A')}")
        print(f"  Class: {form.get('class', 'N/A')}")

        # Ищем поля ввода
        inputs = form.find_all('input')
        if inputs:
            print(f"  Поля ввода ({len(inputs)}):")
            for inp in inputs:
                print(f"    - name='{inp.get('name', 'N/A')}', "
                      f"type='{inp.get('type', 'N/A')}', "
                      f"id='{inp.get('id', 'N/A')}'")

    # Ищем ссылки на авторизацию/вход
    print("\n🔗 ССЫЛКИ НА АВТОРИЗАЦИЮ:")
    login_keywords = ['login', 'auth', 'signin', 'вход', 'войти']
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True).lower()

        if any(keyword in href.lower() or keyword in text for keyword in login_keywords):
            print(f"  {text}: {href}")


def analyze_search(html: str):
    """Анализ функциональности поиска"""
    soup = BeautifulSoup(html, 'lxml')

    print("\n🔎 АНАЛИЗ ПОИСКА:")
    print("=" * 60)

    # Ищем формы поиска
    search_forms = []
    for form in soup.find_all('form'):
        action = str(form.get('action', '')).lower()
        if 'search' in action or 'req' in action:
            search_forms.append(form)

    # Или ищем input с типом search
    search_inputs = soup.find_all('input', {'type': 'search'})
    search_inputs += soup.find_all('input', {'name': lambda x: x and 'search' in x.lower()})

    print(f"Найдено форм поиска: {len(search_forms)}")
    print(f"Найдено полей поиска: {len(search_inputs)}")

    for i, form in enumerate(search_forms, 1):
        print(f"\nФорма поиска #{i}:")
        print(f"  Action: {form.get('action')}")
        print(f"  Method: {form.get('method')}")

        for inp in form.find_all('input'):
            print(f"    - name='{inp.get('name')}', type='{inp.get('type')}'")


def save_html(html: str, filename: str):
    """Сохранить HTML для ручного анализа"""
    output_dir = Path("research_output")
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"💾 Сохранено: {filepath}")


async def main():
    """Главная функция исследования"""
    print("=" * 80)
    print("🔬 ИССЛЕДОВАНИЕ СТРУКТУРЫ ОНЛАЙН.CONSULTANT.RU")
    print("=" * 80)
    print()

    urls_to_check = [
        ("Главная страница", "https://online.consultant.ru"),
        ("Главная (CGI)", "https://online.consultant.ru/cgi/online.cgi?req=home"),
        ("Поиск", "https://online.consultant.ru/cgi/online.cgi?req=doc"),
    ]

    for name, url in urls_to_check:
        print(f"\n{'='*80}")
        print(f"📄 {name}")
        print(f"{'='*80}")

        html, error = await fetch_page(url)

        if html:
            # Анализ
            analyze_login_form(html)
            analyze_search(html)

            # Сохранение
            filename = f"{name.lower().replace(' ', '_')}.html"
            save_html(html, filename)
        else:
            print(f"❌ Не удалось получить страницу: {error}")

        # Задержка между запросами
        await asyncio.sleep(2)

    print("\n" + "="*80)
    print("✅ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
    print("="*80)
    print()
    print("📁 HTML файлы сохранены в: ./research_output/")
    print()
    print("🔍 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Откройте HTML файлы в браузере для визуального анализа")
    print("2. Изучите формы авторизации и поиска")
    print("3. Или откройте сайт в браузере с DevTools (F12)")
    print("   - Попробуйте авторизоваться")
    print("   - Посмотрите во вкладке Network какие запросы отправляются")
    print("   - Обратите внимание на имена полей формы")
    print()


if __name__ == "__main__":
    asyncio.run(main())
