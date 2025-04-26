from discord.channel import TextChannel

from posts import ScheduledPost
from enum import Enum
from typing import Dict

class Channel(Enum):
    MAIN = 1
    BOT = 2

class LeetcodeBot:
    channels: Dict[Channel, TextChannel] = {}
    scheduled_posts: list[ScheduledPost] = []
    uncompleted_questions: set[str] = set()
    completed_questions: set[str] = set()

    # def __init__(self):

    def init(self, main_channel: TextChannel, bot_channel: TextChannel):
        self.channels[Channel.MAIN] = main_channel
        self.channels[Channel.BOT] = bot_channel

    async def send(self, msg: str, channel: Channel):
        await self.channels[channel].send(msg)
