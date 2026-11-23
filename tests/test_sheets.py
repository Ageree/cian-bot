from datetime import datetime
from unittest.mock import Mock, call

import pytest

import sheets
import telegram_notify


HEADER = ["URL", "Added", "Sent", "Next", "Status", "Reply", "Topic"]
URL = "https://cian.ru/sale/flat/123/"


@pytest.fixture
def worksheet(monkeypatch):
    stored_sheet = Mock()
    monkeypatch.setattr(sheets, "_get_sheet", Mock(return_value=stored_sheet))
    monkeypatch.setattr(sheets, "datetime", Mock(now=Mock(return_value=datetime(2026, 4, 10))))
    return stored_sheet


def test_get_sheet_uses_service_account_and_sheet_id(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test-credentials.json")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "test-sheet")
    credentials = Mock()
    authorize = Mock()
    monkeypatch.setattr(sheets.Credentials, "from_service_account_file", credentials)
    monkeypatch.setattr(sheets.gspread, "authorize", authorize)

    assert sheets._get_sheet() is authorize.return_value.open_by_key.return_value.sheet1
    credentials.assert_called_once_with("test-credentials.json", scopes=sheets.SCOPES)
    authorize.assert_called_once_with(credentials.return_value)
    authorize.return_value.open_by_key.assert_called_once_with("test-sheet")


def test_pending_sends_filters_rows_and_initializes_new_listing(worksheet, monkeypatch):
    new_url = "https://cian.ru/sale/flat/456/"
    worksheet.get_all_values.return_value = [
        HEADER,
        [URL, "", "2", "2026-04-10", " Active ", "", " 123 "],
        [URL, "", "invalid", "2026-04-09", "active"],
        [URL, "", "0", "2026-04-11", "active"],
        [URL, "", "1", "2026-04-09", "paused"],
        [URL, "", "1", "2026-04-09", "replied"],
        [URL, "", "20", "2026-04-09", "done"],
        [URL, "", "20", "2026-04-09", "active"],
        [URL, "", "0", "", "active"],
        [],
        ["invalid url"],
        [new_url],
    ]
    create_topic = Mock(return_value=789)
    monkeypatch.setattr(telegram_notify, "create_topic", create_topic)

    assert sheets.get_pending_sends() == [
        {"row": 2, "url": URL, "sent_count": 2, "topic_id": 123},
        {"row": 3, "url": URL, "sent_count": 0, "topic_id": None},
    ]
    assert worksheet.update_cell.call_args_list == [
        call(12, 2, "2026-04-10"),
        call(12, 3, "0"),
        call(12, 4, "2026-04-11"),
        call(12, 5, "active"),
        call(12, 7, "789"),
    ]
    create_topic.assert_called_once_with(new_url)


@pytest.mark.parametrize(
    ("count", "next_date", "status"),
    [(19, "2026-04-14", None), (20, "—", "done")],
)
def test_mark_sent_updates_count_and_next_date(worksheet, count, next_date, status):
    sheets.mark_sent(3, count, days_between=4)

    updates = {
        column: value for row, column, value in (entry.args for entry in worksheet.update_cell.call_args_list)
        if row == 3
    }
    expected = {3: str(count), 4: next_date}
    if status:
        expected[5] = status
    assert updates == expected


def test_mark_replied_and_topic_lookup_normalize_url(worksheet):
    worksheet.get_all_values.return_value = [HEADER, [URL, "", "2", "", "active", "", "123"]]
    variant = "http://www.cian.ru/sale/flat/123"
    assert sheets.get_topic_id(variant) == 123
    assert sheets.get_offer_url_by_topic(123) == URL
    assert sheets.get_offer_url_by_topic(999) is None
    assert sheets.mark_replied(variant, "x" * 110) is True
    assert sheets.mark_replied("https://cian.ru/sale/flat/999/", "hello") is False
    assert worksheet.update_cell.call_args_list == [
        call(2, 5, "replied"), call(2, 4, "—"), call(2, 6, "x" * 100),
    ]


def test_get_stats_counts_nonempty_rows(worksheet):
    worksheet.get_all_values.return_value = [
        HEADER,
        [URL, "", "", "", " Active "],
        [URL, "", "", "", "replied"],
        [URL, "", "", "", "paused"],
        [URL, "", "", "", "done"],
        [URL],
        ["", "", "", "", "active"],
        [],
    ]

    assert sheets.get_stats() == {"total": 5, "active": 1, "replied": 1, "paused": 1, "done": 1}
