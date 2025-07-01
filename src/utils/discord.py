import requests
import logging

log = logging.getLogger("utils/discord.py")


def get_file(url: str):
    log.info(f"Making request to {url}")
    res = requests.get(url)
    log.info(res.status_code)
    return res.content
