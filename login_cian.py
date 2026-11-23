"""
Интерактивный логин в Циан.
Запусти один раз — откроется браузер, залогинься вручную.
Сессия сохранится в файл и будет использоваться ботом.
"""
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from logging_config import configure_logging

load_dotenv()

logger = logging.getLogger(__name__)

SESSION_FILE = os.getenv("CIAN_SESSION_FILE", "cian_session.json")
SESSION_DIR = Path("cian_storage")


def main() -> None:
    logger.info("Логин в Циан: открываю браузер")

    with sync_playwright() as p:
        # Используем persistent context — он сохраняет всё: cookies, localStorage, sessionStorage
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,  # Нужен GUI для ручного логина
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        page = browser_context.new_page()
        page.goto("https://www.cian.ru/authenticate/", wait_until="domcontentloaded")

        input(
            "Войди в Циан в открытом браузере (телефон + SMS).\n"
            "Убедись, что ты вошёл в аккаунт, и нажми Enter здесь... "
        )

        # Проверяем что залогинились — пробуем зайти в диалоги
        page.goto("https://www.cian.ru/dialogs/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Сохраняем cookies отдельно для надёжности
        cookies = browser_context.cookies()
        with open(SESSION_FILE, "w") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        logger.info("Сессия сохранена в %s/ и %s", SESSION_DIR, SESSION_FILE)
        logger.info("Cookies: %s шт.", len(cookies))

        browser_context.close()

    logger.info("Готово! Теперь можешь запускать main.py")


if __name__ == "__main__":
    configure_logging()
    main()
