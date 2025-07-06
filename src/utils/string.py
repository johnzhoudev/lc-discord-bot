from datetime import datetime, time, timedelta
import logging
from typing import Sequence

log = logging.getLogger("utils")


def parse_date_str(date_str: str):
    """
    Parses a string into a `datetime` object, supporting multiple common formats.
    Parses into a single date (no repeats)

    Supported formats (in order of precedence):
        1. "HH:MM" - Interpreted as today's time (schedules for tomorrow if time has already passed today).
        2. "YYYY-MM-DD-HH:MM" - Exact date and time.
        3. "Mon DD, YYYY HH:MM" - Short month name format (e.g., "Jun 21, 2025 14:30").
        4. "Month DD, YYYY HH:MM" - Full month name format (e.g., "June 21, 2025 14:30").
    """
    now = datetime.now()

    try:
        time = datetime.strptime(date_str, "%H:%M")
        newDate = now.replace(
            hour=time.hour, minute=time.minute, second=0, microsecond=0
        )

        if newDate < now:  # schedule for next day
            newDate += timedelta(days=1)

        return newDate
    except ValueError:
        pass

    # Alternatively, try with date
    try:
        newDate = datetime.strptime(date_str, "%Y-%m-%d-%H:%M")
        return newDate
    except ValueError:
        pass

    # Try with regular month name (short form)
    try:
        newDate = datetime.strptime(date_str, "%b %d, %Y %H:%M")
        return newDate
    except ValueError:
        pass

    newDate = datetime.strptime(date_str, "%B %d, %Y %H:%M")
    return newDate


def parse_time_str(time_str: str) -> time:
    return datetime.strptime(time_str, "%H:%M").time()


def parse_days(days_str: str) -> Sequence[int]:
    """
    Outputs list of days, idx
    """
    days_str = days_str.lower()
    if days_str == "daily":
        return range(7)
    elif days_str == "weekdays":
        return range(5)
    elif days_str == "weekends":
        return [5, 6]

    output = []
    days = ["mo", "tu", "we", "th", "fr", "sa", "su"]

    for idx, day in enumerate(days):
        if day in days_str:
            output.append(idx)

    if len(output) == 0:
        raise ValueError(f"{days_str} cannot be parsed")
    return output
