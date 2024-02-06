from pydantic import BaseModel, HttpUrl, Field
import re
from typing import Literal
from models.provider import Provider
from typing_extensions import TypedDict

MAX_NAME_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 280
VALID_CHARACTERS_REGEX = r'^[a-zA-Z0-9\s.,!?:;\'"-]+$'

APIUrlTypes = Literal['openapi']

class Tools(TypedDict):
    tenant: HttpUrl
    tools: list[str]

class Rag(TypedDict):
    host: HttpUrl
    tenant: str
    collections: list[str]

class AgentModel(BaseModel):
    provider_id: str
    model: str
    name_for_human: str
    description_for_human: str
    prompt: str
    prompt_size: int
    tools: list[Tools] = Field(default_factory=list, arbitrary_types_allowed=True)
    rag: list[Rag] = Field(default_factory=list, arbitrary_types_allowed=True)

    def validate(self) -> bool:
        try:
            ToolModel.validate_name_for_human(self.name_for_human)
            ToolModel.validate_description_for_human(self.description_for_human)
            ToolModel.validate_prompt(self.prompt, self.prompt_size)
        except ValueError as e:
            print("Agent model validation error:", e)
            return False
        else:
            return True

    def to_dict(self) -> dict:
        return {
            'provider_id': self.provider_id,
            'model': self.model,
            'name_for_human': self.name_for_human,
            'description_for_human': self.description_for_human,
            'prompt': self.prompt,
            'prompt_size': self.prompt_size,
            'tools': self.tools,
            'rag': self.rag
        }

    @staticmethod
    def validate_name_for_human(name_for_human: str) -> str:
        if not name_for_human:
            raise ValueError('Name for human is required')
        if len(name_for_human) > MAX_NAME_LENGTH:
            raise ValueError('Name for human exceeds maximum length')
        if not re.match(VALID_CHARACTERS_REGEX, name_for_human):
            raise ValueError('Name for human contains invalid characters')
        return name_for_human

    @staticmethod
    def validate_description_for_human(description_for_human: str) -> str:
        if not description_for_human:
            raise ValueError('Description for human is required')
        if len(description_for_human) > MAX_DESCRIPTION_LENGTH:
            raise ValueError('Description for human exceeds maximum length')
        if not re.match(VALID_CHARACTERS_REGEX, description_for_human):
            raise ValueError('Description for human contains invalid characters')
        return description_for_human

    @staticmethod
    def validate_prompt(prompt: str, prompt_size: int) -> str:
        if not prompt:
            raise ValueError('Prompt is required')
        if len(prompt) > prompt_size:
            raise ValueError('Prompt exceeds maximum length')
        return prompt
