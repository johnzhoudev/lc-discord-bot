# For scraping leetcode.com
import json
import re
from dataclasses import dataclass

import requests

@dataclass(frozen=True)
class QuestionData:
    id: int
    title: str
    desc: str
    difficulty: str


def get_question_title_data(titleSlug: str):
    url = "https://leetcode.com/graphql/"
    payload = (
        '{"query":"query questionTitle($titleSlug: String!) {\\n  question(titleSlug: $titleSlug) {\\n    questionId\\n    questionFrontendId\\n    title\\n    titleSlug\\n    isPaidOnly\\n    difficulty\\n    likes\\n    dislikes\\n  }\\n}","variables":{"titleSlug":"'
        + titleSlug
        + '"}}'
    )
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    text = json.loads(response.text)
    return text


def get_question_content_data(titleSlug: str):
    url = "https://leetcode.com/graphql/"
    payload = (
        '{"query":"query questionContent($titleSlug: String!) {\\n  question(titleSlug: $titleSlug) {\\n    content\\n    mysqlSchemas\\n  }\\n}","variables":{"titleSlug":"'
        + titleSlug
        + '"}}'
    )
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    text = json.loads(response.text)
    return text


def get_slug_from_url(url: str):
    return url.split("problems/")[1].split("/")[0]

def scrape_question(url: str):
    slug = get_slug_from_url(url)
    title_data = get_question_title_data(slug)
    content_data = get_question_content_data(slug)

    # format content
    content = content_data["data"]["question"]["content"]
    content = re.sub(r"<[^>]*>", "", content)  # replace all html tags
    content = re.sub(r"&lt;", "<", content)
    content = re.sub(r"&gt;", ">", content)

    return QuestionData(
        title_data["data"]["question"]["questionFrontendId"],
        title_data["data"]["question"]["title"],
        content,
        title_data["data"]["question"]["difficulty"],
    )
