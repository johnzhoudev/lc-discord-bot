import logging
from datetime import datetime, time, timedelta
from typing import Optional, cast

import discord
from discord.channel import TextChannel
from discord.ext import commands, tasks
from dotenv import load_dotenv

from errors import (
    Error,
    FailedScrapeError,
    FailedToParseDateStringError,
    FailedToParseDaysStringError,
    FailedToParseTimeStringError,
    InvalidNumberOfRepeatsError,
    ScheduledDateInPastError,
)
from leetcode_client import scrape_question
from leetcode_bot_logic import Channel, LeetcodeBot
from posts import DateGenerator, Post, ScheduledPost
from text import get_question_text, get_schedule_post_response_text
from utils import get_int_from_env, get_from_env

# Env Setup
load_dotenv()
BOT_TOKEN = get_from_env("BOT_TOKEN")
BOT_CHANNEL_ID = get_int_from_env("BOT_CHANNEL_ID")
MAIN_CHANNEL_ID = get_int_from_env("MAIN_CHANNEL_ID")
TEXT_JSON_FILE = get_from_env("TEXT_JSON_FILE")

# Logging Setup
log = logging.getLogger("Discord Bot")
logging.basicConfig(level=logging.INFO)

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
    # await bot_data.main_channel.send("Hello! LC-Bot is ready!")


# Commmands
async def post_question(post: Post):
    try:
        question_data = scrape_question(post.url)
    except Exception:
        await handle_error(FailedScrapeError(post.url))
        return

    await lc_bot.send(
        get_question_text(question_data.title, post.url, post.desc), Channel.MAIN
    )


@bot.command()
async def post(ctx: commands.Context, url: str, desc: Optional[str] = None):
    # Ignore if not from bot channel
    if ctx.channel != lc_bot.channels[Channel.BOT]:
        return

    await post_question(Post(url, desc))


def parse_date_str(date_str: str):
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

    # Try with regular month name
    newDate = datetime.strptime(date_str, "%b %d, %Y %H:%M")
    return newDate


def parse_time_str(time_str: str) -> time:
    return datetime.strptime(time_str, "%H:%M").time()


def parse_days(days_str: str):
    days_str = days_str.lower()
    if days_str == "daily":
        return range(7)
    elif days_str == "weekdays":
        return range(5)
    elif days_str == "weekends":
        return [5, 6]

    output = []
    days = ["mo", "tu", "we", "th", "fr", "sa", "su"]

    for idx, day in days:
        if day in days_str:
            output.append(idx)

    if len(output) == 0:
        raise ValueError(f"{days_str} cannot be parsed")
    return output


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

    await ctx.send(get_schedule_post_response_text(url, date))


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

    await ctx.send(
        get_schedule_post_response_text("random", should_post.get_next_posting_date())
    )


@bot.command()
async def viewScheduledPosts(ctx):
    msg = "\n".join([f"[{idx}]\t{x}" for idx, x in enumerate(lc_bot.scheduled_posts)])
    await ctx.send(msg)


# Background task to post
@tasks.loop(seconds=3)
async def check_for_scheduled_posts():
    curtime = datetime.now()

    for scheduled_post in lc_bot.scheduled_posts[
        :
    ]:  # make shallow copy so can be removed
        if scheduled_post.should_post(curtime) and (post := scheduled_post.get_post()):
            await post_question(post)
            if scheduled_post.should_delete():
                lc_bot.scheduled_posts.remove(scheduled_post)


bot.run(BOT_TOKEN)
