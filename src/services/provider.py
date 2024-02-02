
from pydantic import BaseModel
import re
from datetime import datetime
from models.provider import ProviderModel
from supabase import  Client
from fyodorov_utils.config.supabase import get_supabase

supabase: Client = get_supabase()


class Provider(BaseModel):
    provider: ProviderModel

    async def update_provider_in_db(self) -> dict:
        if not self.provider.id:
            raise ValueError('Provider ID is required')
        update = {}
        if self.provider.provider_name:
            update['provider_name'] = str(self.provider.provider_name)
        if self.provider.api_url:
            update['api_url'] = str(self.provider.api_url)
        if self.provider.api_key:
            update['api_key'] = self.provider.api_key
        if self.provider.models:
            update['models'] = self.provider.models
        try:
            result = supabase.table('providers').update(update).eq('id', self.provider.id).execute()
            update = result.data[0]
            print('Updated provider:', update)
            return update
        except Exception as e:
            print(f"Error updating provider with id {self.provider.id} "
                  f"and update {update} ")
            raise e

    async def save_provider_in_db(self) -> dict:
        try:
            result = supabase.table('proprovidersvider').insert(self.provider.to_dict()).execute()
            provider = result.data[0]
            print('Saved health update', provider)
            self.provider.id = provider['id']
            return provider
        except Exception as e:
            print('Error saving provider', str(e))
            raise e

    async def delete_provider_in_db(self) -> bool:
        if not self.provider.id:
            raise ValueError('Provider ID is required')
        try:
            result = supabase.table('providers').delete().eq('id', self.provider.id).execute()
            return True
        except Exception as e:
            print('Error deleting provider', str(e))
            raise e

    async def get_provider_by_id(self, id: str) -> dict:
        if not id:
            raise ValueError('Provider ID is required')
        self.provider.id = id
        try:
            result = supabase.table('providers').select('*').eq('id', self.provider.id).limit(1).execute()
            provider = result.data[0]
            return provider
        except Exception as e:
            print('Error fetching provider', str(e))
            raise e

    @staticmethod
    async def get_providers(limit: int = 10, created_at_lt: datetime = datetime.now()) -> [dict]:
        try:
            result = supabase.table('providers') \
                        .select('*') \
                        .order('created_at', desc=True) \
                        .limit(limit) \
                        .lt('created_at', created_at_lt) \
                        .execute()
            data = result.data
            print('Fetched providers', data)
            return data
        except Exception as e:
            print('Error fetching providers', str(e))
            raise e
