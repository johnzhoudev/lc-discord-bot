from typing import Optional
from pydantic import BaseModel, field_validator


class BaseCommandInputModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def set_none_if_x(cls, v):
        return None if v == "x" else v


class PostCommandArgs(BaseCommandInputModel):
    url: str
    date_str: Optional[str] = None
    desc: Optional[str] = None
    story: Optional[str] = None


class CampaignCommandArgs(BaseCommandInputModel):
    time_str: str
    days_str: str
    question_bank_name: str
    length: int
    story_prompt: Optional[str] = None
