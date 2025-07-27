import asyncio
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable, ClassVar, Optional

from src.utils.leetcode_client import LeetcodeClient, QuestionData
from src.types.errors import FailedScrapeError

# Logging Setup
log = logging.getLogger("Discord Bot, Posts")
leetcode_client = LeetcodeClient()


@dataclass
class Post:
    """
    Data class for posts, generated
    """

    id: int = field(init=False)  # Not passed to init
    question_data: QuestionData
    desc: Optional[str] = None
    story: Optional[str] = None

    # Only mutable state
    state_lock = asyncio.Lock()

    def set_id(self, id):
        self.id = id


async def _default_get_story_func(*args):
    return None


class PostGenerator:
    # TODO: Add story generation
    # TODO: Add hint generation

    def __init__(
        self,
        get_url_func: Callable[[], Awaitable[str]],
        desc: Optional[str] = None,
        get_story_func: Callable[
            [QuestionData], Awaitable[str | None]
        ] = _default_get_story_func,  # Accepts QuestionData and story history
    ):
        """
        Only 1 of url or question bank can be specified
        """
        self.get_url_func = get_url_func
        self.desc = desc
        self.get_story_func = get_story_func

    async def __call__(self) -> Post:
        return await self.generate()

    async def generate(self) -> Post:
        url = await self.get_url_func()
        log.info(f"Got url {url}")
        try:
            question_data = leetcode_client.scrape_question(url)
        except Exception:
            raise FailedScrapeError(url)

        return Post(
            question_data=question_data,
            desc=self.desc,
            story=await self.get_story_func(question_data),
        )


class Scheduler:
    """
    Class to use in practice. Sets up internal get_post function and scheduler.
    """

    _id_counter: ClassVar[int] = 0

    id: int
    __get_post_func: Callable[[], Awaitable[Post]]
    __should_post_func: Callable[
        [], bool
    ]  # pass datetime.now, will return True if should post
    repeats: int = 1

    def __init__(
        self,
        get_post_func: Callable[[], Awaitable[Post]],
        should_post_func: Callable[[], bool],
        repeats: int = 1,
    ):
        self.id = (
            Scheduler._id_counter
        )  # One global counter for all Schedulers (even inherited)
        Scheduler._id_counter += 1

        self.__get_post_func = get_post_func
        self.__should_post_func = should_post_func
        self.repeats = repeats

    async def get_post(self):
        if self.repeats == 0:
            return None
        post = await self.__get_post_func()
        if self.repeats > 0:
            self.repeats -= 1  # skip if -1
        return post

    def should_post(self):
        return self.__should_post_func()

    def should_delete(self):
        return self.repeats == 0

    # TODO: Work on this!
    def __str__(self):
        return f"{self.id}: Repeats={self.repeats}"
