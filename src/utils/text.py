from datetime import datetime
from typing import List

from src.internal.posts import Post
from src.internal.question_bank import QuestionBank
import pytz

from src.internal.stats import UserStats


def get_question_text(post: Post):
    date = datetime.now().date().strftime("%B %d, %Y")

    story_text = None
    if post.story:
        story_text = f"\n```\n{post.story}\n```\n"

    return f"""
============================{story_text or ""}
*{date}*
@everyone Leetcode of the day! **{post.question_data.title}**

{post.question_data.url}
{("\n" + post.desc + "\n") if post.desc else ""}
React with :white_check_mark:  if you do it. Also rank personal enjoyment of the problem with :fire:/ :kissing_heart:  or :neutral_face:  or :face_vomiting: or :head_bandage: (messed me up a bit) or :clown: (kinda jokes) or :tropical_drink: (relaxing like ur on vaca). :thought_balloon: (did it in my head)
    """


def get_schedule_post_response_text(url: str, date: datetime):
    return f"Added question: {url} to be posted at {date.strftime('%Y-%m-%d %H:%M')}"


def get_formatted_question_bank_list(banks: List[QuestionBank]):
    eastern_time = pytz.timezone("America/New_York")
    if len(banks) == 0:
        return "No question banks to display."
    bank_lines = [
        f"- {bank.filename} last updated {datetime.strftime(bank.last_updated_time.astimezone(eastern_time), '%Y-%m-%d %H:%M:%S')}"
        for bank in banks
    ]
    msg = "Question banks:\n" + ("\n".join(bank_lines))
    return msg


def get_stats_text(user_stats: List[UserStats]):
    lines = []

    lines.append("Streak")
    user_stats.sort(key=lambda x: x.streak, reverse=True)
    for stat in user_stats:
        lines.append(f"{stat.user_name}: {stat.streak}")

    lines.append("")

    lines.append("Total Completed")
    user_stats.sort(key=lambda x: x.total_completed, reverse=True)
    for stat in user_stats:
        lines.append(f"{stat.user_name}: {stat.total_completed}")

    return "\n".join(lines)
