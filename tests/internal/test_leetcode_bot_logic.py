from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytest_mock
import pytest
import pytest_asyncio

from src.internal.leetcode_bot_logic import Channel, LeetcodeBot
import src.internal.leetcode_bot_logic
import src.utils.string_utils
from src.utils.leetcode_client import QuestionData
from src.internal.posts import Post
import src.internal.posts
from src.types.command_inputs import PostCommandArgs
from tests.test_utils.datetime_test_utils import MockDateTime


@pytest_asyncio.fixture(scope="function")
async def lc_bot(mocker: pytest_mock.MockerFixture, monkeypatch):
    load_dotenv()
    bot = LeetcodeBot(init_openai_client=False)

    # Setup mock channels
    bot_channel = mocker.Mock()
    bot_channel.send = mocker.AsyncMock()
    main_channel = mocker.Mock()
    main_channel.send = mocker.AsyncMock()
    await bot.init(main_channel=main_channel, bot_channel=bot_channel)

    # Mock LC client
    bot.leetcode_client = mocker.Mock()

    # Monkeypatch datetime in LeetcodeBot with MockDateTime
    monkeypatch.setattr(src.internal.leetcode_bot_logic, "datetime", MockDateTime)
    # Monkeypatch datetime in src.utils.string with MockDateTime
    monkeypatch.setattr(src.utils.string_utils, "datetime", MockDateTime)

    yield bot


@pytest.fixture(scope="function")
def posts_lc_client(mocker: pytest_mock.MockerFixture, monkeypatch):
    # Mock lc client
    posts_lc_client_mock = mocker.Mock()
    monkeypatch.setattr(src.internal.posts, "leetcode_client", posts_lc_client_mock)

    yield posts_lc_client_mock


@pytest.mark.asyncio
async def test_send(lc_bot):
    await lc_bot.send("test", Channel.MAIN)
    lc_bot.channels[Channel.MAIN].send.assert_awaited_once_with("test")


@pytest.mark.asyncio
async def test_post_question(lc_bot):
    post = Post(
        QuestionData(1, "title", "question desc", "Easy", "test_url"), "test_desc"
    )

    await lc_bot.post_question(post)
    args, kwargs = lc_bot.channels[Channel.MAIN].send.call_args
    text = args[0]
    assert "test_url" in text
    assert "test_desc" in text


@pytest.mark.asyncio
@pytest.mark.parametrize("date_str", ["x", None])
async def test_handle_post_command_immediate_post(
    date_str, lc_bot, posts_lc_client, mocker: pytest_mock.MockerFixture, monkeypatch
):
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    test_title = "Min moves to equal array"
    test_desc = "What is the min moves to equal array?"

    posts_lc_client.scrape_question.return_value = QuestionData(
        123, test_title, test_desc, "Easy", test_url
    )

    args = PostCommandArgs(
        url=test_url, date_str=date_str, desc="post-desc", story="post-story"
    )

    await lc_bot.handle_post_command(args)

    args, kwargs = lc_bot.channels[Channel.MAIN].send.call_args
    text = args[0]
    assert "post-desc" in text
    assert "post-story" in text
    assert test_url in text
    assert test_title in text
    assert lc_bot.schedulers == []


@pytest.mark.asyncio
async def test_handle_post_command_none_rendered_correctly(
    lc_bot, posts_lc_client, mocker: pytest_mock.MockerFixture, monkeypatch
):
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    test_title = "Min moves to equal array"

    posts_lc_client.scrape_question.return_value = QuestionData(
        123, test_title, "desc", "Easy", test_url
    )

    args = PostCommandArgs(url=test_url, date_str="x", desc=None, story=None)

    await lc_bot.handle_post_command(args)

    args, kwargs = lc_bot.channels[Channel.MAIN].send.call_args
    text = args[0]
    assert "None" not in text
    assert test_url in text
    assert test_title in text


@pytest.mark.asyncio
async def test_handle_post_command_valid_future_schedule(
    lc_bot, posts_lc_client, mocker: pytest_mock.MockerFixture
):
    curr_date = datetime(2025, 6, 26, 9)
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    MockDateTime.init(curr_date)
    posts_lc_client.scrape_question.return_value = QuestionData(
        1, "title", "content", "Easy", test_url
    )
    args = PostCommandArgs(url=test_url, date_str="12:30", desc="desc", story="story")

    await lc_bot.handle_post_command(args)

    await lc_bot.handle_check_for_schedulers()
    lc_bot.channels[Channel.MAIN].send.assert_not_called()

    MockDateTime.advance(timedelta(hours=3))
    await lc_bot.handle_check_for_schedulers()
    lc_bot.channels[Channel.MAIN].send.assert_not_called()

    MockDateTime.advance(timedelta(minutes=31))
    await lc_bot.handle_check_for_schedulers()
    args, kwargs = lc_bot.channels[Channel.MAIN].send.call_args
    question_text = args[0]

    assert test_url in question_text
    assert "desc" in question_text
    assert "story" in question_text


@pytest.mark.asyncio
async def test_handle_post_command_date_in_past(lc_bot, mocker):
    curr_date = datetime(2025, 6, 26, 9)
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    MockDateTime.init(curr_date)

    args = PostCommandArgs(
        url=test_url, date_str="2025-05-26-09:00", desc="desc", story="story"
    )
    await lc_bot.handle_post_command(args)

    args, kwargs = lc_bot.channels[Channel.BOT].send.call_args
    error_text = args[0]
    assert (
        "Scheduled time 2025-05-26 09:00 is in the past. Please provide a time in the future."
        in error_text
    )


@pytest.mark.asyncio
async def test_handle_post_command_invalid_date_str(lc_bot, mocker):
    curr_date = datetime(2025, 6, 26, 9)
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    MockDateTime.init(curr_date)

    args = PostCommandArgs(
        url=test_url, date_str="invalid date", desc="desc", story="story"
    )
    await lc_bot.handle_post_command(args)

    args, kwargs = lc_bot.channels[Channel.BOT].send.call_args
    error_text = args[0]
    assert "Failed to parse date str" in error_text
