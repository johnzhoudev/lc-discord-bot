from datetime import datetime

class Error:
    def __init__(self, msg: str, displayed_msg: str = ""):
        self.msg = msg
        self.displayed_msg = format_error_text(displayed_msg if displayed_msg else msg)

class FailedScrapeError(Error):
    def __init__(self, url: str):
        displayed_msg = f"Failed to scrape question with url {url}"
        super().__init__(displayed_msg)

class ScheduledDateInPastError(Error):
    def __init__(self, date: datetime):
        displayed_msg = f"Scheduled time {date.strftime("%Y-%m-%d %H:%M")} is in the past. Please provide a time in the future."
        super().__init__(displayed_msg)

class FailedToParseDateStringError(Error):
    def __init__(self, date_str: str):
        displayed_msg = """Failed to parse date str. 
Supported formats:
- hh:mm (24 hour)
- yyyy-nn-dd-hh:mm (24 hour)
- Jan 3, 2025 18:30
"""
        super().__init__(f"Failed To Parse date string: {date_str}", displayed_msg)

class FailedToParseTimeStringError(Error):
    def __init__(self, time_str: str):
        displayed_msg = """Failed to parse time str. 
Supported formats:
- hh:mm (24 hour)
"""
        super().__init__(f"Failed To Parse time string: {time_str}", displayed_msg)

class FailedToParseDaysStringError(Error):
    def __init__(self, days_str: str):
        displayed_msg = """Failed to parse days str. 
Supported formats:
- MoTuWeThFrSaSu (Add or remove days as required)
- daily (for all days of the week)
- weekdays (for MoTuWeThFr)
- weekends (for SaSu)
"""
        super().__init__(f"Failed To Parse days string: {days_str}", displayed_msg)

class InvalidNumberOfRepeatsError(Error):
    def __init__(self, rpts: int):
        displayed_msg = "rpts must be >= -1 (-1 = unbounded)"
        super().__init__(f"rpts must be >= -1, {rpts}", displayed_msg)

def format_error_text(msg: str = "An unexpected error occurred"):
    return f"Error: {msg}"
