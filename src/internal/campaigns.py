from src.internal.date_generator import DateGenerator
from src.internal.question_bank_manager import QuestionBankManager


class Campaign:
    def __init__(
        self,
        question_bank_manager: QuestionBankManager,  # Reference
        question_bank_name: str,
        date_generator: DateGenerator,
    ):
        self.question_bank_manager = question_bank_manager
        self.date_generator = date_generator
        self.question_bank_name = question_bank_name

    async def init(self):
        # Create campaign class
        await self.question_bank_manager._assert_question_bank_exists(
            self.question_bank_name
        )
