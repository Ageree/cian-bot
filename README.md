# 🏠 Cian Auto-Messenger

Автоматическая рассылка сообщений собственникам на Циан с Google Sheets интеграцией.

## Quick start (English)

Cian Auto-Messenger sends scheduled follow-ups on Cian, tracks listings in Google
Sheets, and reports replies in a Telegram group.

1. With Python 3.10 or newer, create and activate a virtual environment. Run
   `python -m pip install -r requirements.txt` and `python -m playwright install chromium`.
2. Copy `.env.example` to `.env` and set `GOOGLE_SHEET_ID`, `TELEGRAM_BOT_TOKEN`, and
   `TELEGRAM_GROUP_ID`. Put your Google service-account key in `credentials.json`,
   share the spreadsheet with the service account as an editor, and add the bot
   to a Telegram group with Topics enabled and permission to manage topics.
3. Run `python login_cian.py` from a machine with a graphical display to save
   your Cian session. Then run `python main.py` from the project directory.

For local checks, install `requirements-dev.txt`, then run `ruff check .` and
`python -m pytest`. The tests use mocks for external services.

## Run with Docker Compose

With Docker Compose v2, fill in `.env` and make sure `credentials.json` and
`cian_session.json` are available. The quick start above explains how to create
both files, including the interactive Cian login. From the project directory run:

```sh
docker compose up --build
```

Compose mounts the credentials, session and message templates read-only. The
`bot-state` volume stores the Chromium profile, reply history and application log.
Set `GOOGLE_CREDENTIALS_FILE` or `CIAN_SESSION_FILE` in `.env` to use a different
host file. The container runs as UID/GID 1000 by default. Set `BOT_UID` and
`BOT_GID` before the first build if your files are readable only by a different
non-root user.

## Как работает

1. Ты закидываешь ссылки на объявления Циан в Google Sheets
2. На следующий день в 12:00 отправляется первое сообщение
3. Далее каждые 3 дня — следующее сообщение (до 20 штук)
4. Если собственник ответил — цепочка встаёт на паузу
5. Уведомление в Telegram когда кто-то ответил

## Установка на VPS (Ubuntu)

```bash
# 1. Клонируй проект
git clone <repo> && cd cian-bot

# 2. Python 3.10+ и venv
sudo apt update && sudo apt install python3.10 python3.10-venv -y
python3 -m venv venv
source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# 4. Скопируй и заполни конфиг
cp .env.example .env
nano .env

# 5. Настрой Google Sheets API (см. ниже)

# 6. Первый логин в Циан (интерактивно, нужен дисплей или VNC)
python login_cian.py

# 7. Запуск
python main.py
```

## Настройка Google Sheets

1. Иди на https://console.cloud.google.com/
2. Создай проект → Enable Google Sheets API
3. Создай Service Account → скачай JSON-ключ
4. Назови файл `credentials.json`, положи в корень проекта
5. Открой свою Google таблицу → Поделиться → добавь email сервисного аккаунта
6. ID таблицы из URL: `https://docs.google.com/spreadsheets/d/ЭТОТ_ID/edit`

## Настройка Telegram бота

1. Напиши @BotFather → /newbot → получи токен
2. Добавь бота в группу и отправь сообщение в этой группе
3. Открой `https://api.telegram.org/bot<TOKEN>/getUpdates` → найди chat_id
4. Впиши токен в `TELEGRAM_BOT_TOKEN`, а ID группы — в `TELEGRAM_GROUP_ID` в `.env`

## Структура Google Sheets

| A (Ссылка) | B (Дата добавления) | C (Отправлено) | D (Следующая отправка) | E (Статус) | F (Ответ) |
|---|---|---|---|---|---|
| https://cian.ru/sale/flat/123 | 2025-03-23 | 0 | 2025-03-24 | active | |

- Столбец A заполняешь вручную (ссылки)
- Остальные столбцы заполняются автоматически

## Шаблоны сообщений

Редактируй файл `messages.txt` — каждое сообщение на новой строке, разделитель `---`.
Сообщение №1 отправляется первым, №2 вторым и т.д.
