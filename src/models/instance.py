from pydantic import BaseModel, HttpUrl, Field
import re
from typing import Literal
from models.provider import Provider
from typing_extensions import TypedDict

MAX_TITLE_LENGTH = 80
VALID_CHARACTERS_REGEX = r'^[a-zA-Z0-9\s.,!?:;\'"-]+$'

class InstanceModel(BaseModel):
    id: str | None = None
    agent: str # Links to AgentModel.id
    title: str = ""
    chat_history: str = ""

    def validate(self) -> bool:
        try:
            InstanceModel.validate_title(self.title)
        except ValueError as e:
            print("Instance model validation error:", e)
            return False
        else:
            return True

    def to_dict(self) -> dict:
        return {
            'agent': self.agent.id,
            'title': self.title,
            'history': self.history,
        }

    @staticmethod
    def validate_title(title: str) -> str:
        if not title:
            raise ValueError('Title is required')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValueError('Title exceeds maximum length')
        if not re.match(VALID_CHARACTERS_REGEX, title):
            raise ValueError('Title contains invalid characters')
        return title