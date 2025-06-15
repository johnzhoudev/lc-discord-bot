import argparse
import logging
from datetime import datetime
from typing import Optional, cast

import discord
from discord.channel import TextChannel
from discord.ext import commands, tasks
from dotenv import load_dotenv

from src.errors import (
    Error,
    FailedScrapeError,
    FailedToParseDateStringError,
    FailedToParseDaysStringError,
    FailedToParseTimeStringError,
    InvalidNumberOfRepeatsError,
    ScheduledDateInPastError,
)
from src.leetcode_bot_logic import Channel, LeetcodeBot
from src.posts import DateGenerator, Post, ScheduledPost
from src.text import get_schedule_post_response_text
from src.utils.string import (
    parse_date_str,
    parse_days,
    parse_time_str,
)
from src.utils.boto3 import get_bot_token_from_ssm
from src.utils.environment import (
    get_int_from_env,
    get_from_env,
)

# Logging Setup
log = logging.getLogger("Bot")
logging.basicConfig(level=logging.INFO)
log.info("Starting discord bot")

# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dev", action="store_true", help="Enable development mode")
args = parser.parse_args()
is_dev = args.dev
log.info(f"is_dev: {is_dev}")

# Env Setup
load_dotenv()

if is_dev:
    log.info("Loading bot token from env")
    BOT_TOKEN = get_from_env("BOT_TOKEN")
else:
    log.info("Loading bot token from ssm")
    BOT_TOKEN = get_bot_token_from_ssm()

BOT_CHANNEL_ID = get_int_from_env("BOT_CHANNEL_ID")
MAIN_CHANNEL_ID = get_int_from_env("MAIN_CHANNEL_ID")
TEXT_JSON_FILE = get_from_env("TEXT_JSON_FILE")

# Bot Setup
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

lc_bot = LeetcodeBot()


async def handle_error(error: Error):
    log.error(error.msg)
    await lc_bot.send(error.displayed_msg, Channel.BOT)


@bot.event
async def on_ready():
    log.info("LC-Bot Ready")

    bot_channel = cast(TextChannel, bot.get_channel(BOT_CHANNEL_ID))
    main_channel = cast(TextChannel, bot.get_channel(MAIN_CHANNEL_ID))
    lc_bot.init(main_channel, bot_channel)

    # Start background scheduler
    check_for_scheduled_posts.start()

    await lc_bot.send("Hello! LC-Bot is ready!", Channel.BOT)


@bot.command()
async def post(ctx: commands.Context, url: str, desc: Optional[str] = None):
    # Ignore if not from bot channel
    if ctx.channel != lc_bot.channels[Channel.BOT]:
        return

    try:
        await lc_bot.post_question(Post(url, desc))
    except FailedScrapeError as e:
        await handle_error(e)


@bot.command()
async def schedulePost(ctx, date_str: str, url: str, desc: Optional[str] = None):
    try:
        date = parse_date_str(date_str)
    except Exception:
        await handle_error(FailedToParseDateStringError(date_str))
        return

    if date < datetime.now():
        await handle_error(ScheduledDateInPastError(date))
        return

    def get_post():
        return Post(url, desc)

    def should_post(curtime):
        return curtime < date

    lc_bot.scheduled_posts.append(ScheduledPost(get_post, should_post))

    await lc_bot.send(get_schedule_post_response_text(url, date), Channel.BOT)


@bot.command()
async def scheduleRandom(ctx, time_str: str, days_str: str, rpts: int = -1):
    log.info(f"{time_str}, {days_str}, {rpts}")

    try:
        time = parse_time_str(time_str)
    except ValueError:
        await handle_error(FailedToParseTimeStringError(time_str))
        return

    try:
        days = parse_days(days_str)
    except ValueError:
        await handle_error(FailedToParseDaysStringError(days_str))
        return

    if not rpts >= -1:
        await handle_error(InvalidNumberOfRepeatsError(rpts))
        return

    # TODO: Fix get random post
    def get_post():
        return Post("asdf", "asdf")

    should_post = DateGenerator(days, time, datetime.now())
    lc_bot.scheduled_posts.append(ScheduledPost(get_post, should_post, repeats=rpts))

    await lc_bot.send(
        get_schedule_post_response_text("random", should_post.get_next_posting_date()),
        Channel.BOT,
    )


@bot.command()
async def viewScheduledPosts(ctx):
    msg = "\n".join([f"[{idx}]\t{x}" for idx, x in enumerate(lc_bot.scheduled_posts)])
    await lc_bot.send(msg, Channel.BOT)


# Background task to post
@tasks.loop(seconds=3)
async def check_for_scheduled_posts():
    curtime = datetime.now()

    for scheduled_post in lc_bot.scheduled_posts[
        :
    ]:  # make shallow copy so can be removed
        if scheduled_post.should_post(curtime) and (post := scheduled_post.get_post()):
            try:
                await lc_bot.post_question(post)
            except FailedScrapeError as e:
                await handle_error(e)
                # TODO: Cleanup? Retry?
                return

            if scheduled_post.should_delete():
                lc_bot.scheduled_posts.remove(scheduled_post)


bot.run(BOT_TOKEN)
