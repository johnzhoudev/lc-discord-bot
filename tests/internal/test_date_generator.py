import pytest
from datetime import datetime, time, timedelta

from src.internal.date_generator import DateGenerator
import src.internal.date_generator
from tests.test_utils.datetime_test_utils import MockDateTime


@pytest.fixture(scope="function", autouse=True)
def date_setup(monkeypatch):
    monkeypatch.setattr(src.internal.date_generator, "datetime", MockDateTime)


def test_initial_date_on_valid_day_and_time():
    MockDateTime.init(datetime(2025, 6, 30, 8))  # 8AM Monday
    dg = DateGenerator(days=[0], time=time(9, 0))
    assert dg.get_next_posting_date().weekday() == 0
    assert dg.get_next_posting_date().hour == 9


def test_initial_date_adjusts_to_next_valid_day():
    called_date = datetime(2025, 6, 30, 10)  # 10AM Monday
    MockDateTime.init(called_date)  # 10AM
    dg = DateGenerator(days=[0], time=time(9, 0))
    # Should schedule for next Monday
    assert dg.get_next_posting_date().weekday() == 0
    assert dg.get_next_posting_date() == datetime(2025, 7, 7, 9)


def test_day_generator_cycles_correctly():
    called_date = datetime(2025, 6, 30, 10)  # 10AM Monday
    MockDateTime.init(called_date)  # 10AM
    dg = DateGenerator(days=[1, 3, 5], time=time(9))  # Tuesday, thursday, sat

    assert dg() is False
    MockDateTime.advance(timedelta(days=1))  # Tuesday 10am
    assert dg() is True
    MockDateTime.advance(timedelta(seconds=1))
    assert dg() is False  # Should have advanced to next day
    MockDateTime.advance(timedelta(days=1))  # Wednesday 10am
    assert dg() is False
    MockDateTime.advance(timedelta(days=1))  # Thursday 10am
    assert dg() is True
    MockDateTime.advance(timedelta(days=1))  # Friday 10AM
    assert dg() is False  # Should have advanced to next day
    MockDateTime.advance(timedelta(days=1))  # Sat 10AM
    assert dg() is True
    MockDateTime.advance(timedelta(seconds=1))
    assert dg() is False  # Should have advanced to next day
    MockDateTime.advance(timedelta(days=1))  # Sunday 10am
    assert dg() is False  # Should have advanced to next day
    MockDateTime.advance(timedelta(days=1))  # Monday 10am
    assert dg() is False
    MockDateTime.advance(timedelta(days=1))  # Tuesday 10am
    assert dg() is True


def test_day_generator_returns_true_on_time_single_day():
    called_date = datetime(2025, 6, 30, 9, 59)  # 9:59AM Monday
    MockDateTime.init(called_date)
    dg = DateGenerator(days=[0], time=time(10))  # Monday at 10AM

    assert dg() is False
    MockDateTime.advance(timedelta(minutes=1))
    assert dg() is True
    assert dg() is False  # advanced date generator
    MockDateTime.advance(timedelta(days=2))
    assert dg() is False
    MockDateTime.advance(timedelta(days=4, hours=23, minutes=59))
    assert dg() is False
    MockDateTime.advance(timedelta(minutes=1))
    assert dg() is True
    assert dg() is False


def test_day_generator_all_days():
    called_date = datetime(2025, 6, 30, 9, 59)  # 9:59AM Monday
    MockDateTime.init(called_date)
    dg = DateGenerator(days=[0, 1, 2, 3, 4, 5, 6], time=time(10))  # Monday at 10AM

    for _ in range(12):
        assert dg() is False
        MockDateTime.advance(timedelta(minutes=1))
        assert dg() is True
        assert dg() is False
        MockDateTime.advance(timedelta(minutes=1))
        assert dg() is False
        MockDateTime.advance(timedelta(hours=23, minutes=58))


def test_day_generator_raises_exception_on_no_days():
    with pytest.raises(ValueError):
        DateGenerator(days=[], time=time(9))
