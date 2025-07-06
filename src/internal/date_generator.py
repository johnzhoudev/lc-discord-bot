from datetime import datetime, time, timedelta
from typing import Sequence
import logging

log = logging.getLogger(__name__)


class DateGenerator:
    # days is list of ints representing days to post - 0 = Monday ... 6 = Sunday
    def __init__(self, days: Sequence[int], time: time):
        if len(days) == 0:
            raise ValueError("Days cannot be 0")

        called_date = datetime.now()

        self.day_gen = self.__create_day_generator(days)
        self.time = time
        self.next_date = called_date.replace(
            hour=time.hour, minute=time.minute, second=0, microsecond=0
        )

        # adjust day
        while self.next_date < called_date or self.next_date.weekday() not in days:
            self.next_date = self.next_date + timedelta(days=1)

        while next(self.day_gen) != self.next_date.weekday():
            pass  # advances self.day_gen to match

    def __create_day_generator(self, days: Sequence[int]):
        i = 0
        while True:
            yield days[i]
            i = (i + 1) % len(days)

    def __get_days_to_advance(self, curr_day: int, target_day: int):
        return x if (x := (target_day - curr_day) % 7) != 0 else 7

    def get_next_posting_date(self):
        return self.next_date

    # Returns True if should post, else false
    def __call__(self) -> bool:
        curtime = datetime.now()
        if curtime < self.next_date:  # Not time yet
            return False

        # set next date
        while self.next_date <= curtime:
            self.next_date = self.next_date + timedelta(
                days=self.__get_days_to_advance(
                    self.next_date.weekday(), next(self.day_gen)
                )
            )
        log.info(f"Set next date of date generator to {self.next_date}")
        return True
