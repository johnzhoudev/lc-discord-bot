from datetime import time, datetime
import src.utils

import pytest
from src.utils.string import parse_days, parse_time_str, parse_date_str
import src.utils.string


@pytest.mark.parametrize(
    "days_str, output",
    [
        ("daily", [0, 1, 2, 3, 4, 5, 6]),
        ("weekdays", [0, 1, 2, 3, 4]),
        ("weekends", [5, 6]),
        ("MoTuWe", [0, 1, 2]),
        ("SaSuMo", [0, 5, 6]),
        ("Mon Tue Wed", [0, 1, 2]),
        ("Wednesday Thursday", [2, 3]),
    ],
)
def test_parse_days(days_str, output):
    assert list(parse_days(days_str)) == output


@pytest.mark.parametrize(
    "days_str",
    [
        "asdf",
        "",
    ],
)
def test_parse_days_failures(days_str):
    with pytest.raises(ValueError):
        parse_days(days_str)


@pytest.mark.parametrize(
    "time_str, expected_time",
    [
        ("00:00", time(hour=0, minute=0)),
        ("23:14", time(hour=23, minute=14)),
        ("6:14", time(hour=6, minute=14)),
    ],
)
def test_parse_time_str(time_str, expected_time):
    assert parse_time_str(time_str) == expected_time


@pytest.mark.parametrize("time_str", ["asdf", "", "25:00", "1030", "12:230"])
def test_parse_time_str_failures(time_str):
    with pytest.raises(ValueError):
        parse_time_str(time_str)


@pytest.mark.parametrize(
    "date_str, now_date, expected_date",
    [
        (
            "12:30",
            datetime(2025, 1, 1, 0, 0, 0),
            datetime(2025, 1, 1, 12, 30),
        ),  # expected_date same day
        (
            "09:20",
            datetime(2025, 1, 1, 12, 30, 0),
            datetime(2025, 1, 2, 9, 20),
        ),  # expected_date next day
        (
            "09:20",
            datetime(2025, 1, 1, 9, 20, 0, 1),
            datetime(2025, 1, 2, 9, 20),
        ),  # same date, next day
        # Expect all these to be the same date, irrespective of now
        (
            "2025-09-13-12:30",
            datetime(2025, 9, 13, 9, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "2025-09-13-12:30",
            datetime(2025, 9, 13, 13, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "2025-09-13-12:30",
            datetime(2025, 9, 13, 12, 30, 0, 1),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "Sep 13, 2025 12:30",
            datetime(2025, 9, 13, 9, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "Sep 13, 2025 12:30",
            datetime(2025, 9, 13, 13, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "Sep 13, 2025 12:30",
            datetime(2025, 9, 13, 12, 30, 0, 1),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "September 13, 2025 12:30",
            datetime(2025, 9, 13, 9, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "September 13, 2025 12:30",
            datetime(2025, 9, 13, 13, 0, 0),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "September 13, 2025 12:30",
            datetime(2025, 9, 13, 12, 30, 0, 1),
            datetime(2025, 9, 13, 12, 30),
        ),
        (
            "september 13, 2025 12:30",  # lowercase
            datetime(2025, 9, 13, 12, 30, 0, 1),
            datetime(2025, 9, 13, 12, 30),
        ),
    ],
)
def test_parse_date_str(date_str, now_date, expected_date, monkeypatch):
    # Mock datetime class to override now() to expected date
    class MockDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now_date

    monkeypatch.setattr(src.utils.string, "datetime", MockDateTime)
    assert parse_date_str(date_str) == expected_date


@pytest.mark.parametrize(
    "date_str, now_date",
    [
        ("25:00", datetime(2025, 1, 1)),  # invalid time
        ("00:91", datetime(2025, 1, 1)),  # invalid time
        ("feburary 13, 2025 12:30", datetime(2025, 1, 1)),  # Mispelled months
    ],
)
def test_parse_date_str_failures(date_str, now_date, monkeypatch):
    # Mock datetime class to override now() to expected date
    class MockDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now_date

    monkeypatch.setattr(src.utils.string, "datetime", MockDateTime)

    with pytest.raises(ValueError):
        parse_date_str(date_str)
