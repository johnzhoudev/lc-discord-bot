from typing import Optional
from pydantic import BaseModel, field_validator


class PostCommandArgs(BaseModel):
    url: str
    date_str: Optional[str] = None
    desc: Optional[str] = None
    story: Optional[str] = None

    @field_validator("*", mode="before")
    @classmethod
    def set_none_if_x(cls, v):
        return None if v == "x" else v
