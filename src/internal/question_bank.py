import asyncio
from dataclasses import dataclass
from typing import List
from discord import Attachment
import logging
import csv
from io import StringIO

from src.utils.discord import get_file

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
    csv_data = csv.reader(file, delimiter=",")

    questions = []

    for args in csv_data:
        url = args[0]
        posted = False if len(args) == 1 else bool(args[1])
        questions.append(Question(url=url, posted=posted))

    return QuestionBank(filename=question_file.filename, questions=questions)
