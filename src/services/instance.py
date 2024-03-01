from fastapi import WebSocket
from typing import Union
from datetime import datetime, timedelta
from supabase import Client
from fyodorov_utils.config.supabase import get_supabase
from models.instance import InstanceModel
from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from .agent import Agent
from .provider import Provider
# Models
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain_community.tools import AIPluginTool
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.prompts.chat import ChatPromptTemplate

from fyodorov_llm_agents.agents.openai import OpenAI
from fyodorov_utils.services.tool import Tool

supabase: Client = get_supabase()

JWT = "eyJhbGciOiJIUzI1NiIsImtpZCI6Im14MmVrTllBY3ZYN292LzMiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzA3MzI0MTMxLCJpYXQiOjE3MDczMjA1MzEsImlzcyI6Imh0dHBzOi8vbGptd2R2ZWZrZ3l4cnVjc2dla3cuc3VwYWJhc2UuY28vYXV0aC92MSIsInN1YiI6IjljYzYzOWQ0LWUwMzItNDM3Zi1hNWVhLTUzNDljZGE0YTNmZCIsImVtYWlsIjoiZGFuaWVsQGRhbmllbHJhbnNvbS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7Imludml0ZV9jb2RlIjoiUkFOU09NIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3MDczMjA1MzF9XSwic2Vzc2lvbl9pZCI6ImE4MTM4NmE1LTUxZTUtNDkyMS04ZjM3LWMyYWE3ODlhZDRhZiJ9.NNZA2rm1IQQ9wAhpyC8taMqregRmy8I9oZgT0P5heBg"

class Instance(InstanceModel):
    agent: LLMChain = None

    def get_chat_history(self):
        return [tuple(arr) for arr in self.chat_history]

    async def use_custom_library(self, input: str = "", access_token: str = JWT) -> str:
        agent: AgentModel = Agent.get_in_db(self.agent_id)
        provider = await Provider.get_provider_by_id(agent.provider_id)
        llm = OpenAI(
            api_key=provider.api_key,
            model=agent.model,
            # model="gpt-4",
        )
        for tenant in agent.tools:
            for tool_id in tenant["tools"]:
                print("[use_custom_library] tool id:", tool_id)
                tool = Tool.get_in_db(access_token, tool_id)
                llm.add_tool(tool)
        prompt = f"{agent.prompt}\n\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
        prompt += llm.get_tools_for_prompt()
        print(f"----Prompt----\n{prompt}")
        return llm.invoke(prompt, input)

    async def use_custom_library_async(self, input: str = "", access_token: str = JWT) -> str:
        agent: AgentModel = Agent.get_in_db(self.agent_id)
        provider = await Provider.get_provider_by_id(agent.provider_id)
        llm = Agent(
            api_key=provider.api_key,
            model=agent.model,
            # model="gpt-4",
        )
        for tenant in agent.tools:
            for tool_id in tenant["tools"]:
                print("[use_custom_library] tool id:", tool_id)
                tool = Tool.get_in_db(access_token, tool_id)
                llm.add_tool(tool)
        prompt = f"{agent.prompt}\n\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
        prompt += llm.get_tools_for_prompt()
        async for result in llm.invoke_async(prompt, input):
            yield result

    async def chat_w_fn_calls(self, input: str = "", access_token: str = JWT) -> str:
        agent: AgentModel = Agent.get_in_db(self.agent_id)
        provider = await Provider.get_provider_by_id(agent.provider_id)
        llm = AgentModel(
            api_key=provider.api_key,
            model=agent.model,
            # model="gpt-4",
        )
        prompt = f"{agent.prompt}\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        print(f"----Prompt----\n{prompt}\n---------------\n")
        return llm.call_with_fn_calling(prompt, input)
    
    @staticmethod    
    def create_in_db(instance: InstanceModel) -> str:
        try:
            result = supabase.table('instances').insert(instance.to_dict()).execute()
            print(f"Result of query: {result}")
            # instance_id = result.data[0]['id']
            # return instance_id
        except Exception as e:
            print('Error creating instance', str(e))
            raise e

    @staticmethod
    async def update_in_db(id: str, instance: dict) -> InstanceModel:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').update(instance).eq('id', id).execute()
            print(f"Result of update: {result}")
            return result.data[0]
        except Exception as e:
            print('An error occurred while updating instance:', id, str(e))
            raise

    @staticmethod
    def delete_in_db(id: str) -> bool:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').delete().eq('id', id).execute()
            return True
        except Exception as e:
            print('Error deleting instance', str(e))
            raise e

    @staticmethod
    def get_in_db(id: str) -> InstanceModel:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').select('*').eq('id', id).limit(1).execute()
            instance_dict = result.data[0]
            instance_dict["agent_id"] = str(instance_dict["agent_id"])
            instance_dict["id"] = str(instance_dict["id"])
            print(f"Fetched instance: {instance_dict}")
            instance = InstanceModel(**instance_dict)
            return instance
        except Exception as e:
            print('Error fetching instance', str(e))
            raise e

    @staticmethod
    def get_all_in_db(limit: int = 10, created_at_lt: datetime = datetime.now()) -> [InstanceModel]:
        try:
            result = supabase.from_('instances') \
                .select("*") \
                .limit(limit) \
                .lt('created_at', created_at_lt) \
                .order('created_at', desc=True) \
                .execute()
            instance_models = [InstanceModel(**{k: str(v) if not isinstance(v, list) else v for k, v in instance.items()}) for instance in result.data]
            return instance_models
        except Exception as e:
            print('Error fetching instances', str(e))
            raise e