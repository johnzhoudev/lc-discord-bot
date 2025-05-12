import logging
from discord.channel import TextChannel

from src.errors import FailedScrapeError
from src.leetcode_client import LeetcodeClient
from src.posts import Post, ScheduledPost
from enum import Enum
from typing import Dict

from src.text import get_question_text


class Channel(Enum):
    MAIN = 1
    BOT = 2


class LeetcodeBot:
    channels: Dict[Channel, TextChannel] = {}
    scheduled_posts: list[ScheduledPost] = []
    uncompleted_questions: set[str] = set()
    completed_questions: set[str] = set()
    log: logging.Logger = logging.getLogger("Leetcode Bot")
    leetcode_client = LeetcodeClient()

    def init(self, main_channel: TextChannel, bot_channel: TextChannel):
        self.channels[Channel.MAIN] = main_channel
        self.channels[Channel.BOT] = bot_channel

        self.log.info("Successfully initialized LeetcodeBot")

    async def send(self, msg: str, channel: Channel):
        await self.channels[channel].send(msg)
        self.log.info(f"Sent {msg} to channel {channel}")

    async def post_question(self, post: Post):
        try:
            question_data = self.leetcode_client.scrape_question(post.url)
        except Exception:
            raise FailedScrapeError(post.url)

        await self.send(
            get_question_text(question_data.title, post.url, post.desc), Channel.MAIN
        )
