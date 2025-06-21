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


class LeetcodeClient:
    def __init__(self):
        self.base_url = "https://leetcode.com/graphql/"

    def _get_question_title_data(self, titleSlug: str):
        url = self.base_url
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

    def _get_question_content_data(self, titleSlug: str):
        url = self.base_url
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

    def _get_slug_from_url(self, url: str):
        return url.split("problems/")[1].split("/")[0]

    def scrape_question(self, url: str):
        slug = self._get_slug_from_url(url)
        title_data = self._get_question_title_data(slug)
        content_data = self._get_question_content_data(slug)

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
