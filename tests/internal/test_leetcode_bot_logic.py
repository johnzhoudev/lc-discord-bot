import pytest_mock
import pytest

from src.internal.leetcode_bot_logic import Channel, LeetcodeBot
import src.internal.leetcode_bot_logic
from src.internal.leetcode_client import QuestionData
from src.internal.posts import Post
from src.types.command_inputs import PostCommandArgs


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
        src.internal.leetcode_bot_logic,
        "get_question_text",
        lambda *args, **kwargs: "test_text",
    )
    post = Post(url="test_url", desc="test_desc")

    await lc_bot.post_question(post)
    lc_bot.channels[Channel.MAIN].send.assert_awaited_once_with("test_text")


@pytest.mark.asyncio
@pytest.mark.parametrize("date_str", ["x", None])
async def test_handle_post_command_immediate_post(
    date_str, lc_bot, mocker: pytest_mock.MockerFixture
):
    test_url = "https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/"
    args = PostCommandArgs(url=test_url, date_str=date_str, desc="desc", story="story")

    mock_post_question = mocker.AsyncMock()
    lc_bot.post_question = mock_post_question  # Set method as mock

    await lc_bot.handle_post_command(args)

    mock_post_question.assert_awaited_once()
    post: Post = mock_post_question.call_args[0][0]  # (args, kwargs)
    assert post.desc == "desc"
    assert post.story == "story"
    assert post.url == test_url
    assert lc_bot.schedulers == []


# @pytest.mark.asyncio
# async def test_handle_post_command_valid_future_schedule(lc_bot, mocker: pytest_mock.MockerFixture):
#     future_date = (datetime.now() + timedelta(minutes=10)).strftime("%H:%M")
#     args = PostCommandArgs(
#         url="https://example.com",
#         date_str=future_date,
#         desc="desc",
#         story="story"
#     )

#     lc_bot.send = mocker.AsyncMock()

#     await lc_bot.handle_post_command(args)

#     assert len(lc_bot.schedulers) == 1
#     scheduler = lc_bot.schedulers[0]
#     assert isinstance(scheduler, Scheduler)

#     # should_post should return True after the scheduled time
#     assert scheduler.should_post(datetime.now() + timedelta(minutes=11)) is True

#     lc_bot.send.assert_awaited_once()

# @pytest.mark.asyncio
# async def test_handle_post_command_date_in_past(lc_bot, mocker):
#     past_date = (datetime.now() - timedelta(minutes=10)).strftime("%H:%M")
#     args = PostCommandArgs(
#         url="https://example.com",
#         date_str=past_date,
#         desc="desc",
#         story="story"
#     )

#     lc_bot.handle_error = mocker.AsyncMock()

#     await lc_bot.handle_post_command(args)

#     lc_bot.handle_error.assert_awaited_once()
#     error = lc_bot.handle_error.call_args[0][0]
#     assert isinstance(error, ScheduledDateInPastError)

#     assert lc_bot.schedulers == []

# @pytest.mark.asyncio
# async def test_handle_post_command_invalid_date_str(lc_bot, mocker):
#     args = PostCommandArgs(
#         url="https://example.com",
#         date_str="not-a-date",
#         desc="desc",
#         story="story"
#     )

#     lc_bot.handle_error = mocker.AsyncMock()

#     await lc_bot.handle_post_command(args)

#     lc_bot.handle_error.assert_awaited_once()
#     error = lc_bot.handle_error.call_args[0][0]
#     assert isinstance(error, FailedToParseDateStringError)

#     assert lc_bot.schedulers == []
