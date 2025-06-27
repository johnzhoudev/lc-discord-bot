from datetime import datetime, timedelta
from typing import ClassVar


class MockDateTime(datetime):
    # Class attributes
    curr_date: ClassVar[datetime] = datetime(2025, 6, 26, 9)  # June 26, 2025, 9am

    @classmethod
    def init(cls, curr_date: datetime = datetime(2025, 6, 26, 9)):
        cls.curr_date = curr_date

    @classmethod
    def now(cls):
        return cls.curr_date

    @classmethod
    def advance(cls, time: timedelta):
        cls.curr_date += time
