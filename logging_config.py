"""Настройка логирования для запуска бота и интерактивного входа."""

import logging
import os
import sys

logger = logging.getLogger(__name__)

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class TokenRedactingFormatter(logging.Formatter):
    def __init__(self, token: str) -> None:
        super().__init__(LOG_FORMAT)
        self.token = token

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if self.token:
            # urllib3 logs the request path, which contains the Telegram token.
            return message.replace(self.token, "[REDACTED]")
        return message


def configure_logging(log_file: str | None = None) -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    level = LOG_LEVELS.get(level_name)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    formatter = TokenRedactingFormatter(os.getenv("TELEGRAM_BOT_TOKEN", ""))
    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO if level is None else level,
        handlers=handlers,
    )
    if level is None:
        logger.warning("Некорректный LOG_LEVEL, используется INFO")
