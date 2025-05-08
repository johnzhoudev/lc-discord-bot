from src.leetcode_bot_logic import LeetcodeBot
import pytest


@pytest.fixture
def lc_bot():
    bot = LeetcodeBot()
    yield bot
