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