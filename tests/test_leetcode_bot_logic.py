import pytest_mock
import pytest

from src.leetcode_bot_logic import Channel, LeetcodeBot
import src.leetcode_bot_logic
from src.leetcode_client import QuestionData
from src.posts import Post


@pytest.fixture(scope="function")
def lc_bot(mocker: pytest_mock.MockerFixture):
    bot = LeetcodeBot()

    # Setup mock channels
    bot_channel = mocker.Mock()
    bot_channel.send = mocker.AsyncMock()
    main_channel = mocker.Mock()
    main_channel.send = mocker.AsyncMock()
    bot.init(main_channel=main_channel, bot_channel=bot_channel)

    # Mock LC client
    bot.leetcode_client = mocker.Mock()

    yield bot


@pytest.mark.asyncio
async def test_send(lc_bot):
    await lc_bot.send("test", Channel.MAIN)
    lc_bot.channels[Channel.MAIN].send.assert_awaited_once_with("test")


@pytest.mark.asyncio
async def test_post_question(lc_bot, monkeypatch):
    lc_bot.leetcode_client.scrape_question.return_value = QuestionData(
        1, "title", "content", "Easy"
    )
    monkeypatch.setattr(
        src.leetcode_bot_logic, "get_question_text", lambda *args, **kwargs: "test_text"
    )
    post = Post(url="test_url", desc="test_desc")

    await lc_bot.post_question(post)
    lc_bot.channels[Channel.MAIN].send.assert_awaited_once_with("test_text")
