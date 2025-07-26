import argparse
import functools
import logging
from typing import Optional, cast

import discord
from discord.channel import TextChannel
from discord.ext import commands, tasks
from dotenv import load_dotenv
from discord.raw_models import RawReactionActionEvent

from src.types.command_inputs import CampaignCommandArgs, PostCommandArgs
from src.internal.leetcode_bot_logic import Channel, LeetcodeBot
from src.types.errors import Error, UnexpectedError
from src.utils.boto3 import get_from_ssm
from src.utils.environment import (
    get_int_from_env,
    get_from_env,
)
import src.internal.settings as settings

# Logging Setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Bot")
log.info("Starting discord bot")

# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dev", action="store_true", help="Enable development mode")
args = parser.parse_args()
is_dev = args.dev
log.info(f"is_dev: {is_dev}")

# Must initialize this before anything else
# ie, openai client
settings.initialize(is_dev, is_test=False)

if is_dev:
    # Env Setup
    load_dotenv()
    log.info("Loading bot token from env")
    BOT_TOKEN = get_from_env("BOT_TOKEN")
else:
    log.info("Loading bot token from ssm")
    BOT_TOKEN = get_from_ssm("BOT_TOKEN")

BOT_CHANNEL_ID = get_int_from_env("BOT_CHANNEL_ID")
MAIN_CHANNEL_ID = get_int_from_env("MAIN_CHANNEL_ID")
TEXT_JSON_FILE = get_from_env("TEXT_JSON_FILE")

# Bot Setup
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

lc_bot = LeetcodeBot()


@bot.check
def validate_channel(ctx):
    return ctx.channel.id == BOT_CHANNEL_ID


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        log.warning("Used command in wrong channel.")
    else:
        raise error


@bot.event
async def on_ready():
    log.info("LC-Bot Ready")

    log.info("Getting members")
    members = []
    for guild in bot.guilds:
        log.info(f"Fetching members for: {guild.name}")
        async for member in guild.fetch_members(limit=None):
            if not member.bot:
                members.append(member.name)

    bot_channel = cast(TextChannel, bot.get_channel(BOT_CHANNEL_ID))
    main_channel = cast(TextChannel, bot.get_channel(MAIN_CHANNEL_ID))
    await lc_bot.init(main_channel, bot_channel, members)

    # Start background scheduler
    check_for_schedulers.start()

    await lc_bot.send("Hello! LC-Bot is ready!", Channel.BOT)


# Wrapper for handling unexpected exceptions
def handle_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Error as e:
            await lc_bot.handle_error(e)
        except Exception as e:
            log.exception(f"An unexpected error occurred in {func.__name__}: {e}")
            await lc_bot.handle_error(UnexpectedError())

    return wrapper


@bot.command()
async def test(ctx: commands.Context, prompt: Optional[str] = None):
    res = await lc_bot.test(prompt)
    await lc_bot.send(res, Channel.BOT)


@bot.command()
@handle_exceptions
async def post(
    ctx: commands.Context,
    url: str,
    date_str: Optional[str] = None,
    desc: Optional[str] = None,
    story: Optional[str] = None,
):
    # TODO: Do we need exception handling here?
    # TODO: Do we need to make this non-blocking?
    args = PostCommandArgs(url=url, date_str=date_str, desc=desc, story=story)
    await lc_bot.handle_post_command(args)


@bot.command()
@handle_exceptions
async def uploadQuestionBank(ctx: commands.Context):
    await lc_bot.handle_upload_question_bank(ctx)


@bot.command()
@handle_exceptions
async def listQuestionBanks(ctx: commands.Context):
    await lc_bot.handle_list_question_banks()


@bot.command()
@handle_exceptions
async def getQuestionBank(ctx: commands.Context, question_bank_name: str):
    await lc_bot.handle_get_question_bank(question_bank_name)


@bot.command()
@handle_exceptions
async def deleteQuestionBank(ctx: commands.Context, question_bank_name: str):
    await lc_bot.handle_delete_question_bank(question_bank_name)


@bot.command()
@handle_exceptions
async def listSchedulers(ctx):
    await lc_bot.handle_view_schedulers()


@bot.command()
@handle_exceptions
async def deleteScheduler(ctx, scheduler_id: int):
    await lc_bot.handle_delete_scheduler(scheduler_id)


@bot.command()
@handle_exceptions
async def campaign(
    ctx: commands.Context,
    time_str: str,
    days_str: str,
    question_bank_name: str,
    story_prompt: Optional[str] = None,
    length: int = -1,
):
    """
    If story_prompt is included, then stories will be automatically generated. Otherwise, story will be omitted.
    """
    args = CampaignCommandArgs(
        time_str=time_str,
        days_str=days_str,
        question_bank_name=question_bank_name,
        length=length,
        story_prompt=story_prompt,
    )
    await lc_bot.handle_campaign(args)


@bot.command()
@handle_exceptions
async def stats(ctx: commands.Context):
    await lc_bot.handle_stats()


# Background task to post
@tasks.loop(seconds=30)
@handle_exceptions
async def check_for_schedulers():
    await lc_bot.handle_check_for_schedulers()


@bot.event
async def on_raw_reaction_add(data: RawReactionActionEvent):
    user = await bot.fetch_user(data.user_id)
    message = await lc_bot.channels[Channel.MAIN].fetch_message(data.message_id)

    # Use message id as post id
    await lc_bot.handle_reaction_add(user.name, message.id, str(data.emoji))


@bot.event
async def on_raw_reaction_remove(data: RawReactionActionEvent):
    user = await bot.fetch_user(data.user_id)
    message = await lc_bot.channels[Channel.MAIN].fetch_message(data.message_id)
    await lc_bot.handle_reaction_remove(user.name, message.id, str(data.emoji))


bot.run(BOT_TOKEN)
