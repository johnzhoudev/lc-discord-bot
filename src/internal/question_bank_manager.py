import asyncio
import os
from typing import Dict, Iterable
from discord import Attachment
import logging
import csv
from io import StringIO
from datetime import datetime

from src.constants.config import QUESTION_BANK_DIR
from src.internal.question_bank import Question, QuestionBank
from src.types.errors import (
    FailedToUploadQuestionBankError,
    QuestionBankDoesNotExistError,
)
from src.utils.discord import get_file
from src.utils.text import get_formatted_question_bank_list
from src.utils.validators import is_url

log = logging.getLogger(__name__)


class QuestionBankManager:
    def __init__(self):
        self.question_banks: Dict[str, QuestionBank] = {}
        self.state_lock = asyncio.Lock()

    async def load_question_banks(self):
        async with self.state_lock:
            # Load question banks from file
            log.info(f"Loading question banks from {QUESTION_BANK_DIR}...")
            # Create directories if they don't exist
            os.makedirs(QUESTION_BANK_DIR, exist_ok=True)

            question_banks = os.listdir(QUESTION_BANK_DIR)
            log.info(f"Question banks: {question_banks}")

            for bank in question_banks:
                log.info(f"Loading {QUESTION_BANK_DIR + bank}")
                formatted_question_bank = self._csv_to_question_bank(
                    bank, open(QUESTION_BANK_DIR + bank, "r")
                )
                self.question_banks[bank] = formatted_question_bank

    async def upload_question_bank(self, question_file: Attachment):
        """
        Returns if question bank was updated, or created new
        """
        try:
            question_bank = self._get_question_bank_from_attachment(question_file)
        except ValueError as e:
            log.exception(e)
            raise FailedToUploadQuestionBankError(error_msg=str(e))
        except Exception as e:
            log.exception(e)
            raise FailedToUploadQuestionBankError()

        async with self.state_lock:
            if question_bank.filename in self.question_banks:
                msg = f"Successfully uploaded and replaced question bank with ID: {question_bank.filename}"
            else:
                msg = f"Successfully uploaded question bank with ID: {question_bank.filename}"
            self.question_banks[question_bank.filename] = question_bank

        return msg

    async def get_question_bank_download_url(self, question_bank_name: str) -> str:
        async with self.state_lock:
            await self._assert_question_bank_exists(question_bank_name)
            file_path = self.question_banks[question_bank_name].convert_to_file()
            return file_path

    async def delete_question_bank(self, question_bank_name: str):
        async with self.state_lock:
            await self._assert_question_bank_exists(question_bank_name)

            try:
                os.remove(QUESTION_BANK_DIR + question_bank_name)
            except FileNotFoundError:
                log.warning(f"Tried to delete, File not found for {question_bank_name}")
                pass

            del self.question_banks[question_bank_name]

    async def get_random_question_url_from_question_bank(self, question_bank_name: str):
        async with self.state_lock:
            await self._assert_question_bank_exists(
                question_bank_name=question_bank_name
            )
            return self.question_banks[question_bank_name].get_random_question_url()

    async def get_question_bank_list_text(self):
        async with self.state_lock:
            question_bank_names = list(self.question_banks.values())
            msg = get_formatted_question_bank_list(question_bank_names)
        return msg

    # For internal methods starting with _, lock must be acquired already!
    async def _get_question_bank(self, question_bank_name: str):  # For use by Campaigns
        # STATE LOCK MUST BE ACQUIRED ALREADY
        await self._assert_question_bank_exists(question_bank_name)
        return self.question_banks[question_bank_name]

    async def _assert_question_bank_exists(self, question_bank_name: str):
        """
        raises QuestionBankDoesNotExistError if doesn't exist
        """
        # STATE LOCK MUST BE ACQUIRED ALREADY
        if question_bank_name not in self.question_banks:
            available_question_banks = get_formatted_question_bank_list(
                list(self.question_banks.values())
            )
            raise QuestionBankDoesNotExistError(
                question_bank_name, available_question_banks=available_question_banks
            )

    @staticmethod
    def _get_question_bank_from_attachment(question_file: Attachment) -> QuestionBank:
        # No need for state lock
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
        return QuestionBankManager._csv_to_question_bank(question_file.filename, file)

    @staticmethod
    def _csv_to_question_bank(filename: str, file: Iterable[str]):
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
