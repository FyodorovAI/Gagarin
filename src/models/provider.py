from pydantic import BaseModel, HttpUrl
from typing import Literal

Provider = Literal['openai', 'mistral', 'ollama']

class ProviderModel(BaseModel):
    id: str = None
    name: Provider
    api_key: str
    api_url: HttpUrl | None

    def to_dict(self):
        return {
            'name': self.name,
            'api_key': self.api_key,
            'api_url': str(self.api_url),
        }

    def from_dict(data):
        name = data['name'] if 'name' in data else None
        api_url = data['api_url'] if 'api_url' in data else None
        api_key = data['api_key'] if 'api_key' in data else ""
        return ProviderModel(
            name=name,
            api_key=api_key,
            api_url=api_url,
        )
