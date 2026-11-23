FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    TZ=Europe/Moscow

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && apt-get update \
    && apt-get install -y --no-install-recommends xvfb xauth tzdata \
    && rm -rf /var/lib/apt/lists/*

ARG BOT_UID=1000
ARG BOT_GID=1000
RUN groupadd --gid "$BOT_GID" bot \
    && useradd --uid "$BOT_UID" --gid "$BOT_GID" --create-home bot \
    && install -d -o bot -g bot /data

COPY main.py sheets.py cian_api.py cian_browser.py telegram_bot.py telegram_notify.py logging_config.py ./
USER bot
WORKDIR /data

ENTRYPOINT ["xvfb-run", "-a"]
CMD ["python", "/app/main.py"]
