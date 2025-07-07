import pytest_mock
from src.internal.question_bank import Question, QuestionBank
import src.internal.question_bank
from datetime import datetime


def test_question_bank_random_choice(mocker: pytest_mock.MockerFixture, monkeypatch):
    mock_random = mocker.Mock()
    mock_random.randrange.return_value = 1
    monkeypatch.setattr(src.internal.question_bank, "random", mock_random)

    questions = [Question("q1", False), Question("q2", False), Question("q3", False)]
    bank = QuestionBank("test_file", questions, datetime.now())

    q = bank.get_random_question_url()
    assert q == "q2"
    assert bank.questions[1].posted is True
