from datetime import datetime
from typing import List

from src.internal.posts import Post
from src.internal.question_bank import QuestionBank


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


def get_formatted_question_bank_list(banks: List[QuestionBank]):
    if len(banks) == 0:
        return "No question banks to display."
    bank_lines = [
        f"- {bank.filename} last updated {datetime.strftime(bank.last_updated_time, '%Y-%m-%d %H:%M:%S')}"
        for bank in banks
    ]
    msg = "Question banks:\n" + ("\n-".join(bank_lines))
    return msg
