import re


def is_url(url: str):
    return re.match(r"^https://leetcode\.com/problems/.+", url)
