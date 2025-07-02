import asyncio
from datetime import datetime
import logging
import os
from discord.channel import TextChannel
from discord.ext import commands
from discord import File

from src.constants.config import QUESTION_BANK_DIR
from src.internal.question_bank import (
    QuestionBank,
    csv_to_question_bank,
    get_question_bank_from_attachment,
)
from src.types.command_inputs import PostCommandArgs
from src.types.errors import (
    Error,
    FailedScrapeError,
    FailedToGetPostError,
    FailedToParseDateStringError,
    FailedToUploadQuestionBankError,
    QuestionBankDoesNotExistError,
    ScheduledDateInPastError,
)
from src.internal.leetcode_client import LeetcodeClient
from src.internal.posts import Post, PostGenerator, Scheduler
from enum import Enum
from typing import Dict, Optional

from src.utils.string import parse_date_str
from src.utils.text import (
    get_formatted_question_bank_list,
    get_question_text,
    get_schedule_post_response_text,
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
    question_banks: Dict[str, QuestionBank] = {}

    # For simplicity, just keep one lock and grab it for all state-changing operations
    state_lock = asyncio.Lock()

    def init(self, main_channel: TextChannel, bot_channel: TextChannel):
        self.channels[Channel.MAIN] = main_channel
        self.channels[Channel.BOT] = bot_channel

        self._load_question_banks()

        log.info("Successfully initialized LeetcodeBot")

    async def send(
        self, msg: str, channel: Channel, file_attachment: Optional[str] = None
    ):
        if file_attachment:
            file = File(open(file_attachment, "rb"))
            await self.channels[channel].send(msg, file=file)
        else:
            await self.channels[channel].send(msg)
        log.info(f"Sent {msg} to channel {channel}")

    async def post_question(self, post: Post):
        await self.send(get_question_text(post), Channel.MAIN)

    async def handle_post_command(self, args: PostCommandArgs):
        date = None
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

            def should_post(curtime):
                return curtime > date

            async with self.state_lock:
                self.schedulers.append(
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

    async def handle_upload_question_bank(self, ctx: commands.Context):
        question_file = ctx.message.attachments[0]

        try:
            question_bank = get_question_bank_from_attachment(question_file)
            log.info(question_bank)
        except ValueError as e:
            log.exception(e)
            await self.handle_error(
                FailedToUploadQuestionBankError(), additional_messages=str(e)
            )
            return
        except Exception as e:
            log.exception(e)
            await self.handle_error(FailedToUploadQuestionBankError())
            return

        async with self.state_lock:
            question_bank_exists = question_bank.filename in self.question_banks
            self.question_banks[question_bank.filename] = question_bank

        if question_bank_exists:
            msg = f"Successfully uploaded and replaced question bank with ID: {question_bank.filename}"
        else:
            msg = (
                f"Successfully uploaded question bank with ID: {question_bank.filename}"
            )

        await self.send(msg, Channel.BOT)

    async def handle_get_question_bank(self, question_bank_name: str):
        async with self.state_lock:
            if not await self._check_question_bank_exists(question_bank_name):
                return

            file_path = self.question_banks[question_bank_name].convert_to_file()

        await self.send(
            f"{question_bank_name}:", Channel.BOT, file_attachment=file_path
        )

    async def handle_delete_question_bank(self, question_bank_name: str):
        async with self.state_lock:
            if not await self._check_question_bank_exists(question_bank_name):
                return

            try:
                os.remove(QUESTION_BANK_DIR + question_bank_name)
            except FileNotFoundError:
                log.warning(f"Tried to delete, File not found for {question_bank_name}")
                pass

            del self.question_banks[question_bank_name]

        await self.send(f"{question_bank_name} deleted!", Channel.BOT)

    async def handle_list_question_banks(self):
        async with self.state_lock:
            question_bank_names = list(self.question_banks.keys())

        msg = get_formatted_question_bank_list(question_bank_names)
        await self.send(msg, Channel.BOT)

    async def handle_view_schedulers(self):
        text = (
            "\n".join([str(scheduler) for scheduler in self.schedulers])
            or "No schedulers active."
        )
        await self.send(text, Channel.BOT)

    async def handle_check_for_schedulers(self):
        # TODO: Make this async safe!

        curtime = datetime.now()

        # Make shallow copy so can be reused
        for scheduled_post in self.schedulers[:]:  # noqa
            if not scheduled_post.should_post(curtime):
                continue

            log.info(f"Scheduling post {scheduled_post.id}")
            post = scheduled_post.get_post()

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

    def _load_question_banks(self):
        # Load question banks from file
        log.info(f"Loading question banks from {QUESTION_BANK_DIR}...")
        # Create directories if they don't exist
        os.makedirs(QUESTION_BANK_DIR, exist_ok=True)

        question_banks = os.listdir(QUESTION_BANK_DIR)
        log.info(f"Question banks: {question_banks}")

        for bank in question_banks:
            log.info(f"Loading {QUESTION_BANK_DIR + bank}")
            formatted_question_bank = csv_to_question_bank(
                bank, open(QUESTION_BANK_DIR + bank, "r")
            )
            self.question_banks[bank] = formatted_question_bank

    async def _check_question_bank_exists(self, question_bank_name):
        # STATE LOCK MUST BE ACQUIRED ALREADY
        if question_bank_name not in self.question_banks:
            available_question_banks = get_formatted_question_bank_list(
                list(self.question_banks.keys())
            )
            await self.handle_error(
                QuestionBankDoesNotExistError(question_bank_name),
                additional_messages=available_question_banks,
            )
            return False

        return True
