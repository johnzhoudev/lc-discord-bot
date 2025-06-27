from datetime import datetime

from src.internal.posts import Post


def get_question_text(post: Post):
    date = datetime.now().date().strftime("%B %d, %Y")

    story_text = None
    if post.story:
        story_text = f"\n```\n{post.story}\n```\n"

    return f"""
============================{story_text}
*{date}*
@everyone Leetcode of the day! **{post.question_data.title}**

{post.question_data.url}

{post.desc}

React with :white_check_mark:  if you do it. Also rank personal enjoyment of the problem with :fire:/ :kissing_heart:  or :neutral_face:  or :face_vomiting: or :head_bandage: (messed me up a bit) or :clown: (kinda jokes) or :tropical_drink: (relaxing like ur on vaca). :thought_balloon: (did it in my head)
    """


def get_schedule_post_response_text(url: str, date: datetime):
    return f"Added question: {url} to be posted at {date.strftime('%Y-%m-%d %H:%M')}"
