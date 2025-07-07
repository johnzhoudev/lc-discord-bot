import asyncio
from dataclasses import dataclass
import os
from typing import List
import logging
import csv
import random
from datetime import datetime

from src.constants.config import QUESTION_BANK_DIR
from src.types.errors import NoMoreQuestionsInQuestionBankError

log = logging.getLogger("internal/question_bank.py")

question_bank_lock: asyncio.Lock = asyncio.Lock()


@dataclass
class Question:
    url: str
    posted: bool = False


@dataclass
class QuestionBank:
    filename: str
    questions: List[Question]
    last_updated_time: datetime  # Convert to file, and re-uploaded

    def get_random_question_url(self) -> str:  # Returns file URL
        valid_questions = [
            question for question in self.questions if not question.posted
        ]

        if len(valid_questions) == 0:
            raise NoMoreQuestionsInQuestionBankError(self.filename)

        i = random.randrange(len(valid_questions))
        question = valid_questions[i]
        question.posted = True
        return question.url

    def convert_to_file(self) -> str:  # Returns path to file
        # Write to /data/question_banks/
        rows = [[q.url, q.posted] for q in self.questions]

        # Create directories if they don't exist
        os.makedirs(QUESTION_BANK_DIR, exist_ok=True)

        with open(
            QUESTION_BANK_DIR + self.filename, mode="w", encoding="utf-8"
        ) as file:
            writer = csv.writer(file, delimiter=",", lineterminator="\n")
            writer.writerows(rows)

        self.last_updated_time = datetime.now()

        return QUESTION_BANK_DIR + self.filename
