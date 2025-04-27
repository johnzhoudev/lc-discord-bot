import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Callable, Optional, Sequence

# Logging Setup
log = logging.getLogger("Discord Bot, Posts")
logging.basicConfig(level=logging.INFO)


@dataclass
class Post:
    url: str
    desc: Optional[str] = None


@dataclass
class ScheduledPost:
    __get_post_func: Callable[[], Post]
    __should_post_func: Callable[
        [datetime], bool
    ]  # pass datetime.now, will return bool
    repeats: int = 1

    def __init__(
        self,
        get_post_func: Callable[[], Post],
        should_post_func: Callable[[datetime], bool],
        repeats: int = 1,
    ):
        self.__get_post_func = get_post_func
        self.__should_post_func = should_post_func
        self.repeats = repeats

    def get_post(self):
        if self.repeats == 0:
            return None
        post = self.__get_post_func()
        if self.repeats > 0:
            self.repeats -= 1  # skip if -1
        return post

    def should_post(self, curtime: datetime):
        """
        If should post at specific time
        """
        return self.__should_post_func(curtime)

    def should_delete(self):
        return self.repeats == 0

    # TODO: Work on this!
    def __str__(self):
        return f"{self.repeats}"


class DateGenerator:
    # days is list of ints representing days to post - 0 = Monday ... 6 = Sunday
    def __init__(self, days: Sequence[int], time: time, called_date: datetime):
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
        return (target_day - curr_day) % 7

    def get_next_posting_date(self):
        return self.next_date

    # Returns True if should post, else false
    def __call__(self, curtime: datetime) -> bool:
        if curtime < self.next_date:  # Not time yet
            return False

        # set next date
        self.next_date = self.next_date + timedelta(
            days=self.__get_days_to_advance(
                self.next_date.weekday(), next(self.day_gen)
            )
        )
        log.info(f"Set next date of date generator to {self.next_date}")
        return True
