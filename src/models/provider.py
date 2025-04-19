from pydantic import BaseModel, HttpUrl
from typing import Literal

Provider = Literal['openai', 'mistral', 'ollama', 'openrouter']

class ProviderModel(BaseModel):
    id: str | None = None
    name: Provider
    api_key: str | None = None
    api_url: HttpUrl | None = None

    def to_dict(self):
        dict = {
            'name': self.name.lower(),
        }
        if self.api_url is not None:
            dict['api_url'] = self.api_url
        if self.api_key is not None:
            dict['api_key'] = self.api_key
        if self.id is not None:
            dict['id'] = self.id
        return dict

    def from_dict(data):
        name = data['name'] if 'name' in data else None
        api_url = data['api_url'] if 'api_url' in data else None
        api_key = data['api_key'] if 'api_key' in data else None
        return ProviderModel(
            name=name.lower(),
            api_key=api_key,
            api_url=api_url,
        )
