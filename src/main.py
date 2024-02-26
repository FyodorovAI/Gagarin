from fastapi import FastAPI, Depends, HTTPException, Security, Body, WebSocket, Request
from pydantic import BaseModel, EmailStr
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List
import uvicorn

import os

from fyodorov_utils.auth.auth import authenticate
from fyodorov_utils.decorators.logging import error_handler
from fyodorov_utils.templates.agents import parse_yaml

from services.agent import Agent
from services.instance import Instance
from services.provider import Provider
# from models.agent import AgentModel
from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from models.instance import InstanceModel
from models.provider import ProviderModel


app = FastAPI(title="Gagarin", description="A service for creating and managing chatbots and agents", version="0.0.1")

# Gagarin API
@app.get('/')
@error_handler
def root():
    return 'Gagarin API v1'

@app.get('/health')
@error_handler
def health_check():
    return 'OK'

# Providers endpoints
@app.post('/providers')
@error_handler
async def create_provider(provider: ProviderModel, user = Depends(authenticate)):
    print(f"ProviderModel: {provider}")
    return await Provider.save_provider_in_db(provider)

@app.get('/providers')
@error_handler
async def get_providers(limit: int = 10, created_at_lt: datetime = datetime.now(), user = Depends(authenticate)):
    return await Provider.get_providers(limit = limit, created_at_lt = created_at_lt)

@app.get('/providers/{id}')
@error_handler
async def get_provider(id: str, user = Depends(authenticate)):
    return await Provider.get_provider_by_id(id)

@app.put('/providers/{id}')
@error_handler
async def update_provider(id: str, provider: dict, user = Depends(authenticate)):
    return await Provider.update_provider_in_db(id, update=provider)

@app.delete('/providers/{id}')
@error_handler
async def delete_provider(id: str, user = Depends(authenticate)):
    return await Provider.delete_provider_in_db(id)

# Agents endpoints
@app.post('/agents')
@error_handler
async def create_agent(agent: AgentModel, user = Depends(authenticate)):
    Agent.create_in_db(agent)
    return agent

@app.post('/agents/yaml')
@error_handler
async def create_agent_from_yaml(request: Request, user = Depends(authenticate)):
    try:
        agent_yaml = await request.body()
        parse_yaml(agent_yaml)
    except Exception as e:
        print('Error parsing agents from yaml', str(e))
        raise HTTPException(status_code=400, detail="Invalid YAML format")

@app.post('/agents/from-yaml')
@error_handler
async def create_agent_from_yaml(request: Request, user = Depends(authenticate)):
    try:
        agent_yaml = await request.body()
        agent = AgentModel.from_yaml(agent_yaml)
        return Agent.create_in_db(user['session_id'], agent)
    except Exception as e:
        print('Error creating agent from yaml', str(e))
        raise HTTPException(status_code=400, detail="Invalid YAML format")

@app.get('/agents')
@error_handler
def get_agents(user = Depends(authenticate), limit: int = 10, created_at_lt: datetime = datetime.now()):    
    return Agent.get_all_in_db(limit = limit, created_at_lt = created_at_lt)

@app.get('/agents/{id}')
@error_handler
def get_agent(id: str, user = Depends(authenticate)):
    return Agent.get_in_db(id)

@app.put('/agents/{id}')
@error_handler
def update_agent(id: str, agent: dict, user = Depends(authenticate)):
    return Agent.update_in_db(id, agent)

@app.delete('/agents/{id}')
@error_handler
def delete_agent(id: str, user = Depends(authenticate)):
    return Agent.delete_in_db(id)

# Instances endpoints
@app.post('/instances')
@error_handler
def create_instance(instance: InstanceModel, user = Depends(authenticate)):
    if instance.agent_id not in [str(agent["id"]) for agent in Agent.get_all_in_db()]:
        raise HTTPException(status_code=404, detail="Agent not found")
    Instance.create_in_db(instance)
    return instance

@app.get('/instances')
@error_handler
def get_instances(user = Depends(authenticate), limit: int = 10, created_at_lt: datetime = datetime.now()):
    return Instance.get_all_in_db(limit = limit, created_at_lt = created_at_lt)

@app.get('/instances/{id}')
@error_handler
def get_instance(id: str, user = Depends(authenticate)):
    return Instance.get_in_db(id)

@app.put('/instances/{id}')
@error_handler
def update_instance(id: str, instance: dict, user = Depends(authenticate)):
    return Instance.update_in_db(id, instance)

@app.delete('/instances/{id}')
@error_handler
def delete_instance(id: str, user = Depends(authenticate)):
    return Instance.delete_in_db(id)

# Chat via websocket
# host a websocket where users can send and receive messages from an instance
@app.websocket("/instances/{id}/ws")
async def websocket_endpoint(id: str, websocket: WebSocket):
    await websocket.accept()
    instance_model = Instance.get_in_db(str(id))
    instance = Instance(**instance_model.to_dict())
    await websocket.send_text([f"{tuple_item[0]}:\t {tuple_item[1]}\n" for tuple_item in instance.get_chat_history()])
    while True:
        data = await websocket.receive_text()
        # Process the received message
        # ...
        model_output = await instance.use_custom_library(data)
        await websocket.send_text(model_output)

@app.get("/instances/{id}/stream")
async def multiple_function_calls(id: str, input: str = Body(..., embed=True), user = Depends(authenticate)):
    print(f"ID: {id}")
    print(f"Input: {input}")
    instance_model = Instance.get_in_db(str(id))
    instance = Instance(**instance_model.to_dict())
    return StreamingResponse(instance.use_custom_library_async(input=input, access_token=user['session_id']), media_type="text/plain")

# User endpoints
from fyodorov_utils.auth.endpoints import users_app
app.mount('/users', users_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
