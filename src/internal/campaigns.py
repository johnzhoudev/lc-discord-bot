import logging
from src.internal.date_generator import DateGenerator
from src.internal.posts import PostGenerator, Scheduler
from src.internal.question_bank_manager import QuestionBankManager

log = logging.getLogger(__name__)


class Campaign(Scheduler):
    def __init__(
        self,
        question_bank_manager: QuestionBankManager,  # Reference
        question_bank_name: str,
        date_generator: DateGenerator,
        length: int = -1,  # unlimited
    ):
        self.question_bank_manager = question_bank_manager
        self.question_bank_name = question_bank_name

        # Post generator
        self.post_generator = PostGenerator(self._get_post_url)

        # Date generator
        self.date_generator = date_generator

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
