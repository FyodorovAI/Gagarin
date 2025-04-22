from datetime import datetime
from supabase import Client
from fyodorov_utils.config.supabase import get_supabase
from models.instance import InstanceModel
from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from .agent import Agent
from .provider import Provider

from fyodorov_llm_agents.tools.mcp_tool_service import MCPTool as Tool
from .model import LLM
from models.model import LLMModel

supabase: Client = get_supabase()

JWT = "eyJhbGciOiJIUzI1NiIsImtpZCI6Im14MmVrTllBY3ZYN292LzMiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzA3MzI0MTMxLCJpYXQiOjE3MDczMjA1MzEsImlzcyI6Imh0dHBzOi8vbGptd2R2ZWZrZ3l4cnVjc2dla3cuc3VwYWJhc2UuY28vYXV0aC92MSIsInN1YiI6IjljYzYzOWQ0LWUwMzItNDM3Zi1hNWVhLTUzNDljZGE0YTNmZCIsImVtYWlsIjoiZGFuaWVsQGRhbmllbHJhbnNvbS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7Imludml0ZV9jb2RlIjoiUkFOU09NIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3MDczMjA1MzF9XSwic2Vzc2lvbl9pZCI6ImE4MTM4NmE1LTUxZTUtNDkyMS04ZjM3LWMyYWE3ODlhZDRhZiJ9.NNZA2rm1IQQ9wAhpyC8taMqregRmy8I9oZgT0P5heBg"

class Instance(InstanceModel):

    async def chat_w_fn_calls(self, input: str = "", access_token: str = JWT, user_id: str = "") -> str:
        agent: AgentModel = await Agent.get_in_db(access_token=access_token, id = self.agent_id)
        model: LLMModel = await LLM.get_model(access_token, user_id, id = agent.modelid)
        print(f"Model fetched via LLM.get_model in chat_w_fn_calls: {model}")
        provider: Provider = await Provider.get_provider_by_id(access_token, id = model.provider)
        prompt = f"{agent.prompt}\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        agent.prompt = prompt
        agent.model = model.base_model
        agent.api_key = provider.api_key
        agent.api_url = provider.api_url
        # for index, tool in enumerate(agent.tools):
        #     if isinstance(tool, str):
        #         agent.tools[index] = Tool.get_by_name_and_user_id(access_token, tool, user_id)
        #         print(f"Tool fetched via Tool.get_by_name_and_user_id in chat_w_fn_calls: {agent.tools[index]}")
        res = agent.call_with_fn_calling(input=input, history=self.chat_history)
        self.chat_history.append({
            "role": "user",
            "content": input
        })
        self.chat_history.append({
            "role": "assistant",
            "content": res["answer"]
        })
        # Update history
        self.create_in_db(access_token=access_token, instance=self)
        return res

    @staticmethod
    async def create_in_db(instance: InstanceModel) -> dict:
        try:
            existing_instance = Instance.get_by_title_and_agent(instance.title, instance.agent_id)
            if existing_instance:
                needs_update = False
                for key, value in instance.to_dict().items():
                    if value != existing_instance[key]:
                        print(f"Instance {key} needs updating: {value} != {existing_instance[key]}")
                        needs_update = True
                        existing_instance[key] = value
                if needs_update:
                    print('Instance already exists, will update:', existing_instance)
                    existing_instance["agent_id"] = str(existing_instance["agent_id"])
                    existing_instance["id"] = str(existing_instance["id"])
                    Instance.update_in_db(existing_instance["id"], existing_instance)
                    instance_dict = instance.to_dict()
            else:
                print("Creating instance in DB:", instance.to_dict())
                result = Instance.update_in_db(instance.id, instance.to_dict())
                instance_dict = result.data[0]
            instance_dict["id"] = str(instance_dict["id"])
            instance_dict["agent_id"] = str(instance_dict["agent_id"])
            return instance_dict
        except Exception as e:
            print(f"An error occurred while creating instance: {e}")
            if 'code' in e and e.code == '23505':
                print('Instance already exists')
                instance_dict = Instance.get_by_title_and_agent(instance.title, instance.agent_id)
                return instance_dict
            print('Error creating instance', str(e))
            raise e

    @staticmethod
    async def update_in_db(id: str, instance: dict) -> InstanceModel:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            print(f"Updating instance in DB with ID: {id}, data: {instance}")
            result = supabase.table('instances').update(instance).eq('id', id).execute()
            print(f"Result of update: {result}")
            instance_dict = result.data[0]
            instance_dict["id"] = str(instance_dict["id"])
            return instance_dict
        except Exception as e:
            print('An error occurred while updating instance:', id, str(e))
            raise

    @staticmethod
    async def delete_in_db(id: str) -> bool:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').delete().eq('id', id).execute()
            print('Deleted instance', result)
            if not result.data:
                raise ValueError('Instance ID not found')
            else:
                return True
        except Exception as e:
            print('Error deleting instance', str(e))
            raise e

    @staticmethod
    def get_by_title_and_agent(title: str, agent_id: str) -> dict:
        if not title:
            raise ValueError('Instance title is required')
        if not agent_id:
            raise ValueError('Agent ID is required')
        try:
            result = supabase.table('instances').select('*').eq('title', title).eq('agent_id', agent_id).limit(1).execute()
            instance_dict = result.data[0]
            instance_dict["agent_id"] = str(instance_dict["agent_id"])
            instance_dict["id"] = str(instance_dict["id"])
            print(f"Fetched instance: {instance_dict}")
            return instance_dict
        except Exception as e:
            print('Error fetching instance', str(e))
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