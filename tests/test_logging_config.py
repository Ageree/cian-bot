import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
TOKEN = "123456789:fake-telegram-token"


@pytest.mark.parametrize(
    ("level", "debug_visible", "info_visible", "warning_visible"),
    [
        (None, False, True, False),
        ("  debug  ", True, True, False),
        ("CRITICAL", False, False, False),
        ("invalid-private-value", False, True, True),
    ],
)
def test_startup_logging(tmp_path, level, debug_visible, info_visible, warning_visible):
    env = os.environ.copy()
    env.pop("LOG_LEVEL", None)
    env["PYTHONPATH"] = str(PROJECT_DIR)
    env["TELEGRAM_BOT_TOKEN"] = TOKEN
    dotenv_content = "" if level is None else f'LOG_LEVEL="{level}"\n'
    (tmp_path / ".env").write_text(dotenv_content, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import logging
import os
from dotenv import load_dotenv
from logging_config import configure_logging

load_dotenv(".env")
configure_logging("cian_bot.log")
logger = logging.getLogger("urllib3.connectionpool")
logger.debug("POST /bot%s/getUpdates", os.environ["TELEGRAM_BOT_TOKEN"])
logger.info("startup info")
logger.critical("startup critical")
""",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout == (tmp_path / "cian_bot.log").read_text(encoding="utf-8")
    assert "startup critical" in result.stdout
    assert ("POST /bot[REDACTED]/getUpdates" in result.stdout) is debug_visible
    assert ("startup info" in result.stdout) is info_visible
    assert ("Некорректный LOG_LEVEL" in result.stdout) is warning_visible
    assert TOKEN not in result.stdout
    assert "invalid-private-value" not in result.stdout
