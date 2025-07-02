import asyncio
from dataclasses import dataclass
import os
from typing import Iterable, List
from discord import Attachment
import logging
import csv
from io import StringIO
import random
from datetime import datetime

from src.constants.config import QUESTION_BANK_DIR
from src.types.errors import NoMoreQuestionsInQuestionBankError
from src.utils.discord import get_file
from src.utils.validators import is_url

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

    def get_random_question(self) -> str:  # Returns file URL
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


def get_question_bank_from_attachment(question_file: Attachment) -> QuestionBank:
    log.info("Fetching question file")
    raw_file = get_file(question_file.url)

    log.info("Converting raw file to List of Questions")

    string_content = None
    try:
        log.info("Trying to decode bytes using utf-8")
        string_content = raw_file.decode()
    except UnicodeDecodeError:
        log.warning("Failed to decode using utf-8")
        pass

    if not string_content:
        log.info("Trying to decode bytes using utf-16")
        string_content = raw_file.decode(encoding="utf-16")

    file = StringIO(string_content)
    return csv_to_question_bank(question_file.filename, file)


def csv_to_question_bank(filename: str, file: Iterable[str]):
    csv_data = csv.reader(file, delimiter=",")

    questions = []

    for args in csv_data:
        url = args[0]
        if not is_url(url):
            raise ValueError("Url is not valid!")
        posted = False if len(args) == 1 else bool(args[1])
        questions.append(Question(url=url, posted=posted))

    return QuestionBank(
        filename=filename, questions=questions, last_updated_time=datetime.now()
    )
