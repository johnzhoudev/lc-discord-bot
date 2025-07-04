import pytest
from datetime import datetime, time, timedelta
from typing import Sequence

import pytest_mock

from src.internal.date_generator import DateGenerator
import src.internal.date_generator
from tests.test_utils.datetime_test_utils import MockDateTime

@pytest.fixture(scope="function", autouse=True)
def date_setup(monkeypatch):
    monkeypatch.setattr(src.internal.date_generator, "datetime", MockDateTime)


def test_initial_date_on_valid_day_and_time():
    MockDateTime.init(datetime(2025, 6, 30, 8)) # 8AM Monday
    dg = DateGenerator(days=[0], time=time(9, 0))
    assert dg.get_next_posting_date().weekday() == 0
    assert dg.get_next_posting_date().hour == 9

def test_initial_date_adjusts_to_next_valid_day():
    called_date = datetime(2025, 6, 30, 10)
    MockDateTime.init(called_date) # 10AM
    dg = DateGenerator(days=[0], time=time(9, 0))
    # Should schedule for next Monday
    assert dg.get_next_posting_date().weekday() == 0
    assert dg.get_next_posting_date() == datetime(2025, 7, 7, 9)

def test_initial_date_skips_invalid_days():
    called_date = datetime(2025, 6, 30, 8) # 8AM Monday
    dg = DateGenerator(days=[2, 4], time=time(9, 0))
    assert dg.get_next_posting_date().weekday() == 2
    assert dg.get_next_posting_date() == datetime(2025, 7, 2, 9)

    dg()

# def test_day_generator_cycles_correctly():
#     dg = DateGenerator(days=[1, 3, 5], time=time(9), called_date=make_dt(0, 0))
#     # force advance and test cycle order
#     days = [next(dg.day_gen) for _ in range(6)]
#     assert days == [1, 3, 5, 1, 3, 5]

# def test_call_returns_false_before_next_date():
#     called_date = make_dt(1, 8)  # Tuesday 8am
#     dg = DateGenerator(days=[1], time=time(9, 0), called_date=called_date)
#     cur = make_dt(1, 8, 59)  # 8:59am
#     assert dg(cur) is False

# def test_call_returns_true_at_or_after_next_date():
#     called_date = make_dt(2, 8)  # Wednesday 8am
#     dg = DateGenerator(days=[2], time=time(8, 0), called_date=called_date)
#     cur = make_dt(2, 8, 0)
#     assert dg(cur) is True

# def test_next_date_advances_correctly_on_call():
#     called_date = make_dt(0, 8)  # Monday 8am
#     dg = DateGenerator(days=[0, 2], time=time(8, 0), called_date=called_date)
#     cur = make_dt(0, 8)
#     assert dg(cur) is True
#     # Next should be Wednesday
#     assert dg.get_next_posting_date().weekday() == 2

# def test_wraparound_from_sunday_to_monday():
#     called_date = make_dt(6, 8)  # Sunday
#     dg = DateGenerator(days=[0], time=time(8, 0), called_date=called_date)
#     assert dg.get_next_posting_date().weekday() == 0

# def test_single_day_list_always_same_day():
#     called_date = make_dt(1, 8)
#     dg = DateGenerator(days=[1], time=time(8), called_date=called_date)
#     cur = make_dt(1, 8)
#     assert dg(cur) is True
#     next_date = dg.get_next_posting_date()
#     assert next_date.weekday() == 1
#     assert (next_date - cur).days == 7  # advances by 1 week

# def test_posting_does_not_trigger_seconds_before_time():
#     called_date = make_dt(1, 7)
#     dg = DateGenerator(days=[1], time=time(8, 0), called_date=called_date)
#     cur = dg.get_next_posting_date() - timedelta(seconds=1)
#     assert dg(cur) is False

# def test_posting_triggers_exactly_at_scheduled_time():
#     called_date = make_dt(1, 7)
#     dg = DateGenerator(days=[1], time=time(8, 0), called_date=called_date)
#     cur = dg.get_next_posting_date()
#     assert dg(cur) is True