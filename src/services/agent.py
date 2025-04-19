from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from typing import Union
from datetime import datetime, timedelta
from supabase import  Client
from fyodorov_utils.config.supabase import get_supabase
from fyodorov_llm_agents.tools.tool import Tool as ToolModel
from .model import LLM

supabase: Client = get_supabase()

class Agent(AgentModel):
    @staticmethod    
    async def create_in_db(access_token: str, agent: AgentModel) -> str:
        try:
            supabase = get_supabase(access_token)
            result = supabase.table('agents').upsert(agent.to_dict()).execute()
            agent_id = result.data[0]['id']
            return agent_id
        except Exception as e:
            print('Error creating agent', str(e))
            raise e

    @staticmethod    
    async def create_agent_in_db(access_token: str, agent: dict, user_id: str) -> str:
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
    async def update_in_db(id: str, agent: dict) -> dict:
        if not id:
            raise ValueError('Agent ID is required')
        try:
            result = supabase.table('agents').update(agent).eq('id', id).execute()
            return result.data[0]
        except Exception as e:
            print('An error occurred while updating agent:', id, str(e))
            raise

    @staticmethod
    async def delete_in_db(id: str) -> bool:
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
            agent_dict["modelid"] = str(agent_dict["model_id"])
            model = await LLM.get_model(access_token=access_token, id = agent_dict["modelid"])
            agent_dict['model'] = model.name
            agent = AgentModel(**agent_dict)
            return agent
        except Exception as e:
            print('Error fetching agent', str(e))
            raise e

    @staticmethod
    async def get_all_in_db(limit: int = 10, created_at_lt: datetime = datetime.now()) -> [dict]:
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
        agent_dict['model_id'] = model.id
        del agent_dict['model']
        print('Saving agent', agent_dict)
        agent = await Agent.create_agent_in_db(access_token, agent_dict, user_id)
        return agent

    @staticmethod
    async def get_agent_tools(access_token: str, agent_id: str) -> list:
        if not agent_id:
            raise ValueError('Agent ID is required')
        supabase = get_supabase(access_token)
        result = supabase.table('agent_mcp_tools').select('*').eq('agent_id', agent_id).execute()
        agent = await Agent.get_in_db(access_token, agent_id)
        tools = agent.tools
        return tools

    @staticmethod
    async def assign_agent_tools(access_token: str, agent_id: str, tool_ids: list[ToolModel]) -> list:
        if not tool_ids:
            raise ValueError('Agent IDs are required')
        supabase = get_supabase(access_token)
        result = []
        for tool_id in tool_ids:
            # Check if tool is valid and exists in the database
            tool_result = supabase.table('mcp_tools').select('*').eq('id', tool_id).limit(1).execute()
            if not tool_result.data:
                print(f"Tool with ID {tool_id} does not exist.")
                continue
            supabase.table('agent_mcp_tools').insert({'mcp_tool_id': tool_id, 'agent_id': agent_id}).execute()
            print('Inserted tool', tool_id, 'for agent', agent_id)
            result.append(tool_id)
        return result

    @staticmethod
    async def delete_agent_tool_connection(access_token: str, agent_id: str, tool_id: str) -> list:
        if not agent_id:
            raise ValueError('Agent ID is required')
        if not tool_id:
            raise ValueError('Tool ID is required')
        try:
            supabase = get_supabase(access_token)
            result = supabase.table('agent_mcp_tools').delete().eq('agent_id', agent_id).eq('mcp_tool_id', tool_id).execute()
            return True
        except Exception as e:
            print('Error deleting agent tool', str(e))
            raise e
