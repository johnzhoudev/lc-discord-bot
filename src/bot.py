import argparse
import logging
from typing import Optional, cast

import discord
from discord.channel import TextChannel
from discord.ext import commands, tasks
from dotenv import load_dotenv

from src.types.command_inputs import PostCommandArgs
from src.internal.leetcode_bot_logic import Channel, LeetcodeBot
from src.utils.boto3 import get_bot_token_from_ssm
from src.utils.environment import (
    get_int_from_env,
    get_from_env,
)

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

    bot_channel = cast(TextChannel, bot.get_channel(BOT_CHANNEL_ID))
    main_channel = cast(TextChannel, bot.get_channel(MAIN_CHANNEL_ID))
    lc_bot.init(main_channel, bot_channel)

    # Start background scheduler
    check_for_schedulers.start()

    await lc_bot.send("Hello! LC-Bot is ready!", Channel.BOT)


@bot.command()
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
async def uploadQuestionBank(ctx: commands.Context):
    await lc_bot.handle_upload_question_bank(ctx)


@bot.command()
async def viewSchedulers(ctx):
    await lc_bot.handle_view_schedulers()


# Background task to post
@tasks.loop(seconds=3)
async def check_for_schedulers():
    await lc_bot.handle_check_for_schedulers()


bot.run(BOT_TOKEN)
