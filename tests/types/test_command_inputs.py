from src.types.command_inputs import PostCommandArgs


def test_post_command_args():
    args = PostCommandArgs(
        url="test_url", date_str="date_str", desc="desc", story="story"
    )
    assert args.url == "test_url"
    assert args.date_str == "date_str"
    assert args.desc == "desc"
    assert args.story == "story"


def test_post_command_args_sets_none_if_x():
    args = PostCommandArgs(url="test_url", date_str="x", desc="x", story="x")
    assert args.url == "test_url"
    assert args.date_str is None
    assert args.desc is None
    assert args.story is None
