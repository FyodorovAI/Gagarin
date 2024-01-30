from models.instance import InstanceModel
from typing import Union
from datetime import datetime, timedelta
from supabase import  Client
from config.supabase import get_supabase
# Models
from langchain.agents import AgentExecutor, initialize_agent
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory.buffer import ConversationBufferMemory


supabase: Client = get_supabase()

class Instance():
    instance: InstanceModel

    def chat(self, websocket: WebSocket):
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            
            await websocket.send_text("Response to: " + data)

    def create_model(self):
        # using langchain create a model instance
        agent = Agent.get_in_db(self.agent)
        model = ChatOpenAI(
            model=agent.model,
            openai_api_key=agent_llm.llm.apiKey,
            # streaming=self.enable_streaming,
            temperature=0,
        )

        # Create a memory
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Create a langchain prompt
        prompt = f"{agent.prompt}" f"\n\n{datetime.datetime.now().strftime('%Y-%m-%d')}" f"{instance.chat_history}"

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
                llm=llm,
                memory=memory,
                output_key="output",
                verbose=True,
                prompt=PromptTemplate.from_template(prompt),
            )
            # Create an agent executor by passing in the agent and tools
            # return AgentExecutor(agent=agent, tools=tools, verbose=True, return_only_outputs=True)
        return agent


    def run_model(self, input):
        # Call the agent executor
        agent_executor = self.create_model()
        # Run the agent executor
        agent_executor.invoke(
            {
                "input": input,
            }
        )
        return

    @staticmethod    
    def create_in_db(instance: InstanceModel) -> str:
        try:
            result = supabase.table('instances').insert(instance.to_dict()).execute()
            instance_id = result.data[0]['id']
            return instance_id
        except Exception as e:
            print('Error creating instance', str(e))
            raise e

    @staticmethod
    def update_in_db(id: str, instance: dict) -> dict:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').update(instance).eq('id', id).execute()
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
    def get_in_db(id: str) -> dict:
        if not id:
            raise ValueError('Instance ID is required')
        try:
            result = supabase.table('instances').select('*').eq('id', id).limit(1).execute()
            instance = result.data[0]
            return instance
        except Exception as e:
            print('Error fetching instance', str(e))
            raise e

    @staticmethod
    def get_all_in_db(limit: int = 10, created_at_lt: datetime = datetime.now()) -> [dict]:
        try:
            result = supabase.from_('instances') \
                .select("*") \
                .limit(limit) \
                .lt('created_at', created_at_lt) \
                .order('created_at', desc=True) \
                .execute()
            instances = result.data
            return instances
        except Exception as e:
            print('Error fetching instances', str(e))
            raise e