from pydantic import BaseModel, HttpUrl
from typing import Literal

Provider = Literal['openai']

class ProviderModel(BaseModel):
    id: str | None
    provider_name: Provider
    api_key: str
    api_url: HttpUrl
    models: list[str]
