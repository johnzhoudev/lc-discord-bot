import logging
from typing import List, Optional, override
from src.constants.prompts import (
    STORY_GENERATION_SYSTEM_PROMPT,
    STORY_HISTORY_PROMPT_TEMPLATE,
    USER_STORY_SETUP_PROMPT_DEFAULT,
    USER_STORY_SETUP_PROMPT_TEMPLATE,
    get_story_ending_kickstart_prompt,
    get_story_generation_kickstart_prompt,
)
from src.internal.date_generator import DateGenerator
from src.internal.posts import Post, PostGenerator, Scheduler
from src.internal.question_bank_manager import QuestionBankManager
from src.internal.stats import StatsManager
from src.utils.leetcode_client import QuestionData
from src.utils.openai_client import OpenAIClient
import src.internal.settings as settings

log = logging.getLogger(__name__)


class Campaign(Scheduler):
    def __init__(
        self,
        question_bank_manager: QuestionBankManager,  # Reference
        question_bank_name: str,
        date_generator: DateGenerator,
        stats: StatsManager,
        length: int = -1,  # unlimited
        story_prompt: Optional[str] = None,
    ):
        self.length = length

        self.question_bank_manager = question_bank_manager
        self.question_bank_name = question_bank_name

        self.stats = stats

        # Post generator
        self.post_generator = PostGenerator(
            self._get_post_url, get_story_func=self._get_story
        )

        # Date generator
        self.date_generator = date_generator

        # Stories
        self.story_prompt = story_prompt
        self.story_history: List[str] = []  # Stories for each day so far

        self.openai_client = OpenAIClient()

        # post ids
        self.posts: List[Post] = []

        # Add one repeat for final story ending
        super().__init__(
            self._get_post_func,
            self.date_generator,
            repeats=(length + 1) if length >= 0 else -1,
        )

    async def init(self):
        # Create campaign class
        await self.question_bank_manager._assert_question_bank_exists(
            self.question_bank_name
        )

        log.info("Initialized campaign success")

    async def _get_post_url(self):
        return (
            await self.question_bank_manager.get_random_question_url_from_question_bank(
                self.question_bank_name
            )
        )

    async def _get_post_func(self):
        """
        Add post to internal posts storage
        """
        post = await self.post_generator()
        self.posts.append(post)
        return post

    @override
    def should_post(self):
        # TODO: Disable?
        if settings.is_dev:
            return True
        return self._should_post_func()

    @override
    def should_final_post(self):
        return self.repeats == 1

    @override
    async def get_final_post(self):
        res = await self._get_story(None)  # Ending
        # Have to type it like this and pass None, can' specify a python function type for kwargs
        self.repeats -= 1
        return res

    async def _get_story(self, question_data: QuestionData | None):
        # This class should have exclusive access over its story_history, so no need for locks
        # If question data is not passed, will generate ending story
        setup_prompt = (
            USER_STORY_SETUP_PROMPT_TEMPLATE.format(self.story_prompt)
            or USER_STORY_SETUP_PROMPT_DEFAULT
        )

        inputs = [
            {
                "role": "system",
                "content": STORY_GENERATION_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": setup_prompt,
            },
        ]

        # Optionally add history
        if self.story_history:
            history = {
                "role": "user",
                "content": STORY_HISTORY_PROMPT_TEMPLATE.format(
                    "\n".join(self.story_history)
                ),
            }
            inputs.append(history)

        # User completion
        percent_complete = None
        if self.posts:
            last_post = self.posts[-1]
            post_id = last_post.id
            # Post id is actually okay to access, even if campaigns may update id. This is because in asyncio event loop,
            # this task will run until the next await. So it can't be pre-empted. So we're fine to access here.
            # post_id should be updated as soon as the post is sent. Will raise attribute error if it doesn't.
            num_complete, num_total = await self.stats.get_num_users_finished_question(
                post_id
            )
            percent_complete = num_complete / num_total
            log.info(
                f"num_complete: {num_complete}, num_total: {num_total}, percent: {percent_complete}"
            )

        kickstart_prompt = None
        if question_data:
            # Kickstart prompt
            kickstart_prompt = get_story_generation_kickstart_prompt(
                question_data.desc,
                len(self.story_history) + 1,
                self.length,  # Including ending
                last_story_percent_complete=percent_complete,
            )
        else:
            # Story ending
            kickstart_prompt = get_story_ending_kickstart_prompt(
                last_story_percent_complete=percent_complete,
            )

        inputs.append({"role": "user", "content": kickstart_prompt})

        log.info("Running story generation with the following:")
        log.info(inputs)

        res = self.openai_client.generate(inputs)
        log.info(res)
        log.info(res.output_text)

        # Add to story history
        self.story_history.append(res.output_text)

        return res.output_text
