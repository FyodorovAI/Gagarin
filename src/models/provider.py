from pydantic import BaseModel, HttpUrl
from typing import Literal

Provider = Literal['openai']

class ProviderModel(BaseModel):
    name: Provider
    api_key: str
    api_url: HttpUrl

    def to_dict(self):
        return {
            'name': self.name,
            'api_key': self.api_key,
            'api_url': str(self.api_url),
        }
