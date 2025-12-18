#!/usr/bin/env python3
"""
Исследование страницы авторизации login.consultant.ru
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
from pathlib import Path


def fetch_login_page():
    """Получить страницу авторизации"""
    url = "https://login.consultant.ru/"

    print(f"📡 Запрос: {url}")
    print("   Используем curl-cffi с имитацией браузера...")

    try:
        # Пробуем разные версии браузеров
        browsers = ["chrome110", "chrome116", "chrome120", "safari15_5"]

        for browser in browsers:
            print(f"\n   Попытка с {browser}...")

            response = requests.get(
                url,
                impersonate=browser,
                timeout=15,
                allow_redirects=True,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                }
            )

            print(f"   Статус: {response.status_code}")

            if response.status_code == 200:
                print(f"   ✅ Успех с {browser}!")
                return response.text, response.url
            elif response.status_code == 403:
                print(f"   ❌ 403 Forbidden")
                continue
            else:
                print(f"   ⚠️  Неожиданный статус: {response.status_code}")

        return None, None

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None, None


def analyze_login_form(html: str, final_url: str):
    """Детальный анализ формы авторизации"""
    soup = BeautifulSoup(html, 'lxml')

    print("\n" + "="*80)
    print("🔍 АНАЛИЗ СТРАНИЦЫ АВТОРИЗАЦИИ")
    print("="*80)
    print(f"Финальный URL: {final_url}")
    print()

    # Поиск всех форм
    forms = soup.find_all('form')
    print(f"📋 Найдено форм на странице: {len(forms)}\n")

    for i, form in enumerate(forms, 1):
        print(f"{'─'*80}")
        print(f"ФОРМА #{i}")
        print(f"{'─'*80}")

        # Атрибуты формы
        print(f"  Action: {form.get('action', 'НЕТ')}")
        print(f"  Method: {form.get('method', 'НЕТ')}")
        print(f"  ID: {form.get('id', 'НЕТ')}")
        print(f"  Class: {form.get('class', 'НЕТ')}")
        print(f"  Name: {form.get('name', 'НЕТ')}")

        # Все поля ввода
        inputs = form.find_all('input')
        print(f"\n  📝 Поля ввода ({len(inputs)}):")

        for inp in inputs:
            inp_type = inp.get('type', 'text')
            inp_name = inp.get('name', 'НЕТ ИМЕНИ')
            inp_id = inp.get('id', '')
            inp_value = inp.get('value', '')
            inp_placeholder = inp.get('placeholder', '')

            print(f"    • type='{inp_type}', name='{inp_name}'")
            if inp_id:
                print(f"      id='{inp_id}'")
            if inp_value:
                print(f"      value='{inp_value}'")
            if inp_placeholder:
                print(f"      placeholder='{inp_placeholder}'")

        # Кнопки
        buttons = form.find_all('button')
        if buttons:
            print(f"\n  🔘 Кнопки ({len(buttons)}):")
            for btn in buttons:
                print(f"    • type='{btn.get('type', 'НЕТ')}', text='{btn.get_text(strip=True)}'")

        # Submit inputs
        submits = form.find_all('input', {'type': 'submit'})
        if submits:
            print(f"\n  ✅ Submit кнопки ({len(submits)}):")
            for sub in submits:
                print(f"    • name='{sub.get('name', 'НЕТ')}', value='{sub.get('value', 'НЕТ')}'")

        print()

    # Поиск ключевых элементов
    print(f"{'─'*80}")
    print("🔑 ВАЖНЫЕ ЭЛЕМЕНТЫ:")
    print(f"{'─'*80}")

    # Поля логина
    login_fields = soup.find_all('input', {'type': ['text', 'email']})
    login_fields += soup.find_all('input', attrs={'name': lambda x: x and ('login' in x.lower() or 'user' in x.lower() or 'email' in x.lower())})

    if login_fields:
        print("  📧 Возможные поля логина:")
        for field in login_fields:
            print(f"    • name='{field.get('name')}', type='{field.get('type')}', id='{field.get('id')}'")

    # Поля пароля
    password_fields = soup.find_all('input', {'type': 'password'})
    if password_fields:
        print("\n  🔒 Поля пароля:")
        for field in password_fields:
            print(f"    • name='{field.get('name')}', id='{field.get('id')}'")

    # CSRF токены
    csrf_fields = soup.find_all('input', {'type': 'hidden'})
    csrf_fields += soup.find_all('input', attrs={'name': lambda x: x and ('csrf' in x.lower() or 'token' in x.lower())})

    if csrf_fields:
        print("\n  🛡️  CSRF/Hidden поля:")
        for field in csrf_fields:
            print(f"    • name='{field.get('name')}', value='{field.get('value', '')[:50]}...'")

    # JavaScript события
    print("\n  ⚙️  JavaScript события:")
    onsubmit_forms = soup.find_all('form', attrs={'onsubmit': True})
    if onsubmit_forms:
        print(f"    Найдено {len(onsubmit_forms)} форм с onsubmit")

    print()


def save_html(html: str, filename: str = "login_page.html"):
    """Сохранить HTML"""
    output_dir = Path("research_output")
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"💾 HTML сохранён: {filepath}")
    print(f"   Откройте в браузере для визуального просмотра")
    print()


def main():
    print("="*80)
    print("🔬 ИССЛЕДОВАНИЕ СТРАНИЦЫ АВТОРИЗАЦИИ login.consultant.ru")
    print("="*80)
    print()

    html, final_url = fetch_login_page()

    if html:
        analyze_login_form(html, final_url)
        save_html(html)

        print("="*80)
        print("✅ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
        print("="*80)
        print()
        print("📋 СЛЕДУЮЩИЙ ШАГ:")
        print("   1. Проверьте research_output/login_page.html")
        print("   2. Используйте найденные имена полей для адаптации scraper")
        print()
    else:
        print()
        print("="*80)
        print("❌ НЕ УДАЛОСЬ ПОЛУЧИТЬ СТРАНИЦУ")
        print("="*80)
        print()
        print("🔧 АЛЬТЕРНАТИВНЫЙ ПОДХОД:")
        print("   1. Откройте https://login.consultant.ru/ в браузере")
        print("   2. Нажмите F12 → вкладка Elements/Элементы")
        print("   3. Найдите <form> элемент (Ctrl+F, поиск 'form')")
        print("   4. Правый клик на <form> → Copy → Copy outerHTML")
        print("   5. Отправьте мне скопированный HTML")
        print()


if __name__ == "__main__":
    main()
