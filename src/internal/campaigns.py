import logging
from typing import List, Optional, override
from src.constants.prompts import (
    STORY_GENERATION_SYSTEM_PROMPT,
    STORY_HISTORY_PROMPT_TEMPLATE,
    USER_STORY_SETUP_PROMPT_DEFAULT,
    USER_STORY_SETUP_PROMPT_TEMPLATE,
    get_story_generation_kickstart_prompt,
)
from src.internal.date_generator import DateGenerator
from src.internal.posts import PostGenerator, Scheduler
from src.internal.question_bank_manager import QuestionBankManager
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
        length: int = -1,  # unlimited
        story_prompt: Optional[str] = None,
    ):
        self.length = length

        self.question_bank_manager = question_bank_manager
        self.question_bank_name = question_bank_name

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

        super().__init__(self.post_generator, self.date_generator, repeats=length)

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

    @override
    def should_post(self):
        # TODO: Disable?
        if settings.is_dev:
            return True
        return self.__should_post_func()

    def _get_story(self, question_data: QuestionData):
        # This class should have exclusive access over its story_history, so no need for locks
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

        inputs.append(
            {
                "role": "user",
                "content": get_story_generation_kickstart_prompt(
                    question_data.desc, len(self.story_history) + 1, self.length
                ),
            }
        )

        log.info("Running story generation with the following:")
        log.info(inputs)

        res = self.openai_client.generate(inputs)
        log.info(res)
        log.info(res.output_text)

        # Add to story history
        self.story_history.append(res.output_text)

        return res.output_text
