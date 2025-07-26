import asyncio
from datetime import datetime
import logging
from discord.channel import TextChannel
from discord.ext import commands
from discord import File

from src.internal.campaigns import Campaign
from src.internal.date_generator import DateGenerator
from src.internal.question_bank_manager import QuestionBankManager
from src.internal.stats import StatsManager
from src.types.command_inputs import CampaignCommandArgs, PostCommandArgs
from src.types.errors import (
    Error,
    FailedScrapeError,
    FailedToGetPostError,
    FailedToParseDateStringError,
    FailedToParseDaysStringError,
    FailedToParseTimeStringError,
    ScheduledDateInPastError,
)
from src.utils.leetcode_client import LeetcodeClient
from src.internal.posts import Post, PostGenerator, Scheduler
import src.internal.settings as settings
from enum import Enum
from typing import Dict, Optional

from src.utils.openai_client import OpenAIClient
from src.utils.string_utils import parse_date_str, parse_days, parse_time_str
from src.utils.text import (
    get_question_text,
    get_schedule_post_response_text,
    get_stats_text,
)


class Channel(Enum):
    MAIN = 1
    BOT = 2


log = logging.getLogger("LeetcodeBot (Internal Logic)")


class LeetcodeBot:
    channels: Dict[Channel, TextChannel] = {}
    schedulers: list[Scheduler] = []
    uncompleted_questions: set[str] = set()
    completed_questions: set[str] = set()
    leetcode_client = LeetcodeClient()
    question_bank_manager = QuestionBankManager()
    stats = StatsManager()

    # For simplicity, just keep one lock and grab it for all state-changing operations
    state_lock = asyncio.Lock()

    def __init__(self):
        if settings.is_test:
            return

        # Init here on creation, not definition
        self.openai_client = OpenAIClient()

    async def init(
        self, main_channel: TextChannel, bot_channel: TextChannel, members: list[str]
    ):
        self.channels[Channel.MAIN] = main_channel
        self.channels[Channel.BOT] = bot_channel

        await self.question_bank_manager.load_question_banks()

        await self.stats.init(members)

        log.info("Successfully initialized LeetcodeBot")

    async def send(
        self, msg: str, channel: Channel, file_attachment: Optional[str] = None
    ):
        if file_attachment:
            file = File(open(file_attachment, "rb"))
            res = await self.channels[channel].send(msg, file=file)
        else:
            res = await self.channels[channel].send(msg)
        log.info(f"Sent {msg} to channel {channel}, id {res.id}")
        return res

    async def post_question(self, post: Post):
        message = await self.send(get_question_text(post), Channel.MAIN)
        post.set_id(
            message.id
        )  # Posts aren't really stored anywhere, so maybe this is redundant for now
        await self.stats.handle_new_post(message.id)

    async def handle_post_command(self, args: PostCommandArgs):
        date = None

        async def get_post_url():
            return args.url

        def get_story(*func_args):
            return args.story

        if args.date_str:
            try:
                date = parse_date_str(args.date_str)
            except Exception as e:
                log.exception(e)
                await self.handle_error(FailedToParseDateStringError(args.date_str))
                return

            if date < datetime.now():
                await self.handle_error(ScheduledDateInPastError(date))
                return

            def should_post():
                return datetime.now() > date

            await self.add_to_schedulers(
                Scheduler(
                    PostGenerator(
                        get_post_url, desc=args.desc, get_story_func=get_story
                    ),
                    should_post,
                )
            )

            await self.send(
                get_schedule_post_response_text(args.url, date), Channel.BOT
            )
        else:
            # Immediately post question

            # TESTING: Use question bank
            # question_bank = self.question_banks[args.url]
            # try:
            #     post = PostGenerator(lambda: question_bank.get_random_question_url(), desc=args.desc, get_story_func=lambda: args.story)()
            # except Error as e:
            #     log.exception(e)
            #     await self.handle_error(e)
            #     return

            post = await PostGenerator(
                get_post_url, desc=args.desc, get_story_func=get_story
            )()
            await self.post_question(post)

    async def handle_upload_question_bank(self, ctx: commands.Context):
        question_file = ctx.message.attachments[0]
        response = await self.question_bank_manager.upload_question_bank(question_file)
        await self.send(response, Channel.BOT)

    async def handle_get_question_bank(self, question_bank_name: str):
        file_path = await self.question_bank_manager.get_question_bank_download_url(
            question_bank_name
        )
        await self.send(
            f"{question_bank_name}:", Channel.BOT, file_attachment=file_path
        )

    async def handle_delete_question_bank(self, question_bank_name: str):
        await self.question_bank_manager.delete_question_bank(question_bank_name)
        await self.send(f"{question_bank_name} deleted!", Channel.BOT)

    async def handle_list_question_banks(self):
        msg = await self.question_bank_manager.get_question_bank_list_text()
        await self.send(msg, Channel.BOT)

    async def handle_view_schedulers(self):
        text = (
            "\n".join([str(scheduler) for scheduler in self.schedulers])
            or "No schedulers active."
        )
        await self.send(text, Channel.BOT)

    async def handle_check_for_schedulers(self):
        # TODO: Make this async safe!

        # Make shallow copy so can be reused
        for scheduled_post in self.schedulers[:]:  # noqa
            if not scheduled_post.should_post():
                continue

            log.info(f"Scheduling post {scheduled_post.id}")
            post = await scheduled_post.get_post()

            if not post:
                await self.handle_error(FailedToGetPostError(scheduled_post.id))
                continue

            try:
                await self.post_question(post)
            except FailedScrapeError as e:
                await self.handle_error(e, f"Removing question {scheduled_post}")
                self.schedulers.remove(scheduled_post)
                continue

            if scheduled_post.should_delete():
                self.schedulers.remove(scheduled_post)

    async def handle_campaign(
        self,
        args: CampaignCommandArgs,
    ):
        # parse time and day
        try:
            time = parse_time_str(args.time_str)
        except ValueError:
            raise FailedToParseTimeStringError(args.time_str)

        try:
            days = parse_days(args.days_str)
        except ValueError:
            raise FailedToParseDaysStringError(args.days_str)

        # Generate date
        date_generator = DateGenerator(days, time)

        campaign = Campaign(
            self.question_bank_manager,
            args.question_bank_name,
            date_generator,
            length=args.length,
            story_prompt=args.story_prompt,
        )
        await campaign.init()

        # TODO: Add to scheduler, and add to scheduling loop
        # Add to scheduler
        await self.add_to_schedulers(campaign)

        await self.send("Successfully added campaign to schedulers", Channel.BOT)

        # await self.send(str(time), Channel.BOT)
        # await self.send(str(days), Channel.BOT)

    async def handle_reaction_add(self, user_name: str, post_id: int, emoji: str):
        await self.stats.log_user_reaction_add(user_name, post_id, emoji)

    async def handle_reaction_remove(self, user_name: str, post_id: int, emoji: str):
        await self.stats.log_user_reaction_remove(user_name, post_id, emoji)

    async def handle_stats(self):
        user_stats = await self.stats.get_user_stats()
        text = get_stats_text(user_stats)
        await self.send(text, Channel.BOT)

    async def test(self, prompt: Optional[str]):
        client = OpenAIClient()
        res = client.test(prompt)
        return res

    async def handle_error(
        self, error: Error, additional_messages: Optional[str] = None
    ):
        # WARNING: DO NOT ACQURIE STATE LOCK HERE!
        log.error(error.msg)
        log.info(additional_messages)
        displayed_msg = error.displayed_msg + (
            f"\n{additional_messages}" if additional_messages else ""
        )
        await self.send(displayed_msg, Channel.BOT)

    async def add_to_schedulers(self, scheduler: Scheduler):
        async with self.state_lock:
            self.schedulers.append(scheduler)
