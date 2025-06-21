from datetime import datetime
import logging
from discord.channel import TextChannel

from src.types.command_inputs import PostCommandArgs
from src.types.errors import (
    Error,
    FailedScrapeError,
    FailedToParseDateStringError,
    ScheduledDateInPastError,
)
from src.internal.leetcode_client import LeetcodeClient
from src.internal.posts import Post, PostGenerator, Scheduler
from enum import Enum
from typing import Dict

from src.utils.string import parse_date_str
from src.utils.text import get_question_text, get_schedule_post_response_text


class Channel(Enum):
    MAIN = 1
    BOT = 2


log = logging.getLogger("LeetcodeBot (Internal Logic)")


class LeetcodeBot:
    channels: Dict[Channel, TextChannel] = {}
    scheduled_posts: list[Scheduler] = []
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

    async def handle_post_command(self, args: PostCommandArgs):
        date = None
        if args.date_str:
            try:
                date = parse_date_str(args.date_str)
            except Exception:
                await self.handle_error(FailedToParseDateStringError(args.date_str))
                return

            if date < datetime.now():
                await self.handle_error(ScheduledDateInPastError(date))
                return

            def should_post(curtime):
                return curtime < date

            self.scheduled_posts.append(
                Scheduler(
                    PostGenerator(args.url, desc=args.desc, story=args.story),
                    should_post,
                )
            )
            await self.send(
                get_schedule_post_response_text(args.url, date), Channel.BOT
            )
        else:
            # Immediately post question
            post = PostGenerator(**args.model_dump(exclude_none=True))()
            await self.post_question(post)

    async def handle_error(self, error: Error):
        log.error(error.msg)
        await self.send(error.displayed_msg, Channel.BOT)
