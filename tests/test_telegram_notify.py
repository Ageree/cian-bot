import json
from http import HTTPStatus
from unittest.mock import Mock, call

import pytest
import requests

import telegram_notify


def response(status: int, payload: dict | None = None) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode() if payload is not None else b"<html>"
    return result


@pytest.fixture
def telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_GROUP_ID", "-100123")
    post = Mock()
    sleep = Mock()
    monkeypatch.setattr(telegram_notify.requests, "post", post)
    monkeypatch.setattr(telegram_notify.time, "sleep", sleep)
    return post, sleep


def test_notification_retries_transient_errors_then_succeeds(telegram):
    post, sleep = telegram
    post.side_effect = [
        requests.Timeout(),
        response(HTTPStatus.BAD_GATEWAY),
        response(HTTPStatus.OK, {"ok": True, "result": {"message_id": 42}}),
    ]

    telegram_notify.send_to_topic(12, "Test message")

    assert post.call_args_list == [
        call(
            "https://api.telegram.org/botfake-token/sendMessage",
            json={
                "chat_id": "-100123",
                "message_thread_id": 12,
                "text": "Test message",
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
    ] * 3
    assert sleep.call_args_list == [call(1), call(2)]


@pytest.mark.parametrize("status", [HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.OK])
def test_notification_honors_telegram_retry_after(telegram, status):
    post, sleep = telegram
    post.side_effect = [
        response(status, {"ok": False, "error_code": 429, "parameters": {"retry_after": 8}}),
        response(HTTPStatus.OK, {"ok": True, "result": {"message_id": 42}}),
    ]

    telegram_notify.send_to_general("Test message")

    assert post.call_count == 2
    sleep.assert_called_once_with(8)


def test_notification_stops_after_four_attempts(telegram, caplog):
    post, sleep = telegram
    post.side_effect = requests.ConnectionError("URL contains fake-token")

    telegram_notify.send_to_general("Test message")

    assert post.call_count == 4
    assert sleep.call_args_list == [call(1), call(2), call(4)]
    assert "ConnectionError" in caplog.text
    assert "fake-token" not in caplog.text


def test_notification_does_not_retry_permanent_error(telegram):
    post, sleep = telegram
    post.return_value = response(HTTPStatus.BAD_REQUEST, {"ok": False, "error_code": 400})

    telegram_notify.send_to_general("Test message")

    assert post.call_count == 1
    sleep.assert_not_called()


def test_topic_creation_is_not_retried(telegram):
    post, sleep = telegram
    post.side_effect = requests.Timeout()

    assert telegram_notify.create_topic("https://cian.ru/sale/flat/123/") is None

    assert post.call_count == 1
    sleep.assert_not_called()
