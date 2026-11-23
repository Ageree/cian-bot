from unittest.mock import Mock, call

import pytest

import main


@pytest.fixture
def configured_env(monkeypatch):
    # Spell out the expected keys so the tests catch a change in the contract.
    for key in ("GOOGLE_SHEET_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID"):
        monkeypatch.setenv(key, "configured")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("GOOGLE_SHEET_ID", None),
        ("TELEGRAM_BOT_TOKEN", ""),
        ("TELEGRAM_GROUP_ID", "   "),
    ],
)
def test_startup_reports_missing_config(configured_env, monkeypatch, caplog, key, value):
    if value is None:
        monkeypatch.delenv(key)
    else:
        monkeypatch.setenv(key, value)
    scheduler = Mock()
    monkeypatch.setattr(main, "BackgroundScheduler", scheduler)

    with pytest.raises(SystemExit) as exit_info:
        main.main()

    assert exit_info.value.code == 1
    assert key in caplog.text
    assert ".env" in caplog.text
    scheduler.assert_not_called()


@pytest.mark.parametrize("custom", [False, True], ids=["defaults", "custom"])
def test_main_registers_schedule(configured_env, monkeypatch, tmp_path, custom):
    for name in ("CIAN_SESSION_FILE", "GOOGLE_CREDENTIALS_FILE"):
        path = tmp_path / name
        path.touch()
        monkeypatch.setenv(name, str(path))
    hour, minute, interval = (9, 15, 25) if custom else (12, 0, 60)
    for name, value in zip(
        ("SEND_HOUR", "SEND_MINUTE", "CHECK_REPLIES_INTERVAL_MINUTES"),
        (hour, minute, interval),
    ):
        if custom:
            monkeypatch.setenv(name, str(value))
        else:
            monkeypatch.delenv(name, raising=False)

    scheduler_class = Mock()
    monkeypatch.setattr(main, "BackgroundScheduler", scheduler_class)
    monkeypatch.setattr(main.telegram_notify, "send_to_general", Mock())
    polling = Mock(side_effect=KeyboardInterrupt)
    monkeypatch.setattr(main.telegram_bot, "run_polling", polling)

    main.main()

    scheduler_class.assert_called_once_with(timezone="Europe/Moscow")
    scheduler = scheduler_class.return_value
    assert [(job.args, {k: v for k, v in job.kwargs.items() if k != "name"})
            for job in scheduler.add_job.call_args_list] == [
        ((main.task_send_messages, "cron"), {"hour": hour, "minute": minute, "id": "send_messages"}),
        ((main.task_check_replies, "interval"), {"minutes": interval, "id": "check_replies"}),
        ((main.task_daily_stats, "cron"), {"hour": 20, "minute": 0, "id": "daily_stats"}),
    ]
    scheduler.start.assert_called_once_with()
    polling.assert_called_once_with()
    scheduler.shutdown.assert_called_once_with()


def test_send_task_cycles_templates_and_updates_only_successes(monkeypatch):
    first_url = "https://cian.ru/sale/flat/123/"
    second_url = "https://cian.ru/sale/flat/456/"
    pending = [
        {"row": 2, "url": first_url, "sent_count": 2, "topic_id": 100},
        {"row": 3, "url": second_url, "sent_count": 1, "topic_id": 200},
    ]
    monkeypatch.setenv("DAYS_BETWEEN_MESSAGES", "4")
    monkeypatch.setattr(main, "load_messages", Mock(return_value=["First", "Second"]))
    get_pending = Mock(return_value=pending)
    mark_sent = Mock()
    send = Mock(side_effect=[{"success": True}, {"success": False, "error": "failed"}])
    notify = Mock()
    sleep = Mock()
    monkeypatch.setattr(main.sheets, "get_pending_sends", get_pending)
    monkeypatch.setattr(main.sheets, "mark_sent", mark_sent)
    monkeypatch.setattr(main.cian_api, "send_message", send)
    monkeypatch.setattr(main.telegram_notify, "notify_send_result", notify)
    monkeypatch.setattr(main.random, "randint", Mock(return_value=45))
    monkeypatch.setattr(main.time, "sleep", sleep)

    main.task_send_messages()

    get_pending.assert_called_once_with(4)
    assert send.call_args_list == [call(first_url, "First"), call(second_url, "Second")]
    mark_sent.assert_called_once_with(2, 3, 4)
    assert notify.call_args_list == [
        call(100, first_url, 3, True),
        call(200, second_url, 2, False, "failed"),
    ]
    sleep.assert_called_once_with(45)


def test_send_task_reports_sheet_error(monkeypatch):
    monkeypatch.setattr(main, "load_messages", Mock(return_value=["First"]))
    monkeypatch.setenv("DAYS_BETWEEN_MESSAGES", "3")
    monkeypatch.setattr(main.sheets, "get_pending_sends", Mock(side_effect=RuntimeError("offline")))
    notify = Mock()
    send = Mock()
    monkeypatch.setattr(main.telegram_notify, "send_to_general", notify)
    monkeypatch.setattr(main.cian_api, "send_message", send)

    main.task_send_messages()

    notify.assert_called_once_with("Ошибка чтения таблицы: offline")
    send.assert_not_called()
