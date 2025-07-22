import logging
from openai import OpenAI

from src.utils.boto3 import get_from_ssm
from src.utils.environment import get_from_env
import src.internal.settings as settings

log = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        if settings.is_dev:
            log.info("Creating openai client using dev flag")
            api_key = get_from_env("OPENAI_API_KEY")
        else:
            api_key = get_from_ssm("OPENAI_API_KEY")

        self.client = OpenAI(api_key=api_key)
        # self.model = "gpt-4.1-mini"
        self.model = "gpt-4.1"

    def generate(self, inputs):
        response = self.client.responses.create(model=self.model, input=inputs)
        return response

    def test(self, prompt=None):
        response = self.client.responses.create(
            model=self.model,
            input=(
                (prompt or "Write a story about a leetcode question two sum")
                + " And make it maximum 1500 characters"
            ),
        )
        log.info(response.output_text)
        return response.output_text
