from fastapi import WebSocket
from typing import Union
from datetime import datetime, timedelta
from supabase import Client
from fyodorov_utils.config.supabase import get_supabase
from models.instance import InstanceModel
from .agent import Agent
from .provider import Provider
# Models
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate

supabase: Client = get_supabase()

class Instance(InstanceModel):
    agent: LLMChain = None

    async def chat(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text("Hello World!")
        while True:
            data = await websocket.receive_text()
            
            await websocket.send_text("Response to: " + data)

    async def create_model(self):
        # using langchain create a model instance
        agent: AgentModel = Agent.get_in_db(self.agent_id)
        provider = await Provider.get_provider_by_id(agent.provider_id)
        model = ChatOpenAI(
            model=agent.model,
            openai_api_key=provider.api_key,
            # streaming=self.enable_streaming,
            temperature=0,
        )

        # Create a memory
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Create a langchain prompt
        prompt = f"{agent.prompt}" f"\n\n{datetime.now().strftime('%Y-%m-%d')}" f"{self.chat_history}"

        # Create a list of Tools
        tools = []

        if len(tools) > 0:
            # Construct the OpenAI Tools agent
            agent = initialize_agent(
                agent_kwargs={
                    "system_message": prompt,
                    "extra_prompt_messages": [
                        MessagesPlaceholder(variable_name="chat_history")
                    ],
                },
            )
        else:
            agent = LLMChain(
                llm=model,
                output_key="output",
                verbose=True,
                prompt=PromptTemplate.from_template(prompt),
            )
        return agent


    async def run_model(self, input) -> str:
        # Run the agent executor
        try:
            self.chat_history = f"{self.chat_history}\n{input}"
            self.agent = await self.create_model()
            result = await self.agent.ainvoke({})
            print(f"Result: {result}")
            self.chat_history = f"{self.chat_history}\n{result['output']}"
            await self.update_in_db(self.id, {"chat_history": self.chat_history})
            return result["output"]
        except Exception as e:
            print('An error occurred while running model:', str(e))

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
            instance_models = [InstanceModel(**instance) for instance in result.data]
            return instance_models
        except Exception as e:
            print('Error fetching instances', str(e))
            raise e