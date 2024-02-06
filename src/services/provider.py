
from pydantic import BaseModel
import re
from datetime import datetime
from models.provider import ProviderModel
from supabase import  Client
from fyodorov_utils.config.supabase import get_supabase

supabase: Client = get_supabase()


class Provider(ProviderModel):
    provider: ProviderModel

    @staticmethod
    async def update_provider_in_db(id: str, update: dict) -> dict:
        if not id:
            raise ValueError('Provider ID is required')
        try:
            result = supabase.table('providers').update(update).eq('id', id).execute()
            update = result.data[0]
            print('Updated provider:', update)
            return update
        except Exception as e:
            print(f"Error updating provider with id {id} "
                  f"and update {update} ")
            raise e

    @staticmethod
    async def save_provider_in_db(provider: ProviderModel) -> dict:
        try:
            result = supabase.table('providers').insert(provider.to_dict()).execute()
            provider = result.data[0]
            print('Saved health update', provider)
            return provider
        except Exception as e:
            print('Error saving provider', str(e))
            raise e

    @staticmethod
    async def delete_provider_in_db(id) -> bool:
        if not id:
            raise ValueError('Provider ID is required')
        try:
            result = supabase.table('providers').delete().eq('id', id).execute()
            return True
        except Exception as e:
            print('Error deleting provider', str(e))
            raise e

    @staticmethod
    async def get_provider_by_id(id: str) -> dict:
        if not id:
            raise ValueError('Provider ID is required')
        try:
            result = supabase.table('providers').select('*').eq('id', id).limit(1).execute()
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
