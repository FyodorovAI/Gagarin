from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from typing import Union
from datetime import datetime, timedelta
from supabase import  Client
from fyodorov_utils.config.supabase import get_supabase
from .model import LLM

supabase: Client = get_supabase()

class Agent(AgentModel):
    @staticmethod    
    def create_in_db(access_token: str, agent: AgentModel) -> str:
        try:
            supabase = get_supabase(access_token)
            result = supabase.table('agents').upsert(agent.to_dict()).execute()
            agent_id = result.data[0]['id']
            return agent_id
        except Exception as e:
            print('Error creating agent', str(e))
            raise e

    @staticmethod    
    def create_agent_in_db(access_token: str, agent: dict, user_id: str) -> str:
        try:
            supabase = get_supabase(access_token)
            agent['user_id'] = user_id
            result = supabase.table('agents').upsert(agent).execute()
            agent_dict = result.data[0]
            return agent_dict
        except Exception as e:
            print('Error creating agent', str(e))
            raise e

    @staticmethod
    def update_in_db(id: str, agent: dict) -> dict:
        if not id:
            raise ValueError('Agent ID is required')
        try:
            result = supabase.table('agents').update(agent).eq('id', id).execute()
            return result.data[0]
        except Exception as e:
            print('An error occurred while updating agent:', id, str(e))
            raise

    @staticmethod
    def delete_in_db(id: str) -> bool:
        if not id:
            raise ValueError('Agent ID is required')
        try:
            result = supabase.table('agents').delete().eq('id', id).execute()
            return True
        except Exception as e:
            print('Error deleting agent', str(e))
            raise e

    @staticmethod
    async def get_in_db(access_token: str, id: str) -> AgentModel:
        if not id:
            raise ValueError('Agent ID is required')
        try:
            supabase = get_supabase(access_token)
            result = supabase.table('agents').select('*').eq('id', id).limit(1).execute()
            agent_dict = result.data[0]
            print(f"Fetched agent: {agent_dict}")
            agent_dict["modelid"] = str(agent_dict["modelid"])
            model = await LLM.get_model(access_token=access_token, id = agent_dict["modelid"])
            agent_dict['model'] = model.name
            agent = AgentModel(**agent_dict)
            return agent
        except Exception as e:
            print('Error fetching agent', str(e))
            raise e

    @staticmethod
    def get_all_in_db(limit: int = 10, created_at_lt: datetime = datetime.now()) -> [dict]:
        try:
            result = supabase.from_('agents') \
                .select("*") \
                .limit(limit) \
                .lt('created_at', created_at_lt) \
                .order('created_at', desc=True) \
                .execute()
            agents = result.data
            print(f"Fetched agents: {agents}")
            return agents
        except Exception as e:
            print('Error fetching agents', str(e))
            raise e

    @staticmethod
    async def save_from_dict(access_token: str, user_id: str, data):
        agent = AgentModel.from_dict(data)
        model_name = data['model']
        model = await LLM.get_model(access_token, user_id, model_name)
        agent_dict = agent.to_dict()
        agent_dict['modelid'] = model.id
        del agent_dict['model']
        print('Saving agent', agent_dict)
        agent = Agent.create_agent_in_db(access_token, agent_dict, user_id)
        return agent