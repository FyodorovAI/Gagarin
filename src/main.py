from fastapi import FastAPI, Depends, HTTPException, Security, Body, WebSocket, Request
from fastapi import Request
from pydantic import BaseModel, EmailStr
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List
import uvicorn
import yaml
import re

import os

from fyodorov_utils.auth.auth import authenticate
from fyodorov_utils.decorators.logging import error_handler

from services.agent import Agent
from services.instance import Instance
from services.provider import Provider
# from models.agent import AgentModel
from fyodorov_llm_agents.agents.agent import Agent as AgentModel
from fyodorov_llm_agents.tools.tool import Tool as ToolModel
from models.instance import InstanceModel
from models.provider import ProviderModel
from services.provider import Provider
from services.model import LLMModel
from services.model import LLM


app = FastAPI(title="Gagarin", description="A service for creating and managing chatbots and agents", version="0.0.1")
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request here
    print(f"Request: {request.method} {request.url}")
    print(f"Headers: {request.headers}")
    print(f"Body: {await request.body()}")
    
    response = await call_next(request)
    
    return response

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
async def create_provider(provider: ProviderModel, request: Request, user = Depends(authenticate)):
    print(f"User: {user}")
    if "localhost" in str(provider.api_url):  
        print("Replacing IP in API URL")      
        # Get the IP address of the user
        print(f"Request: {request.headers}")
        if "X-Forwarded-For"  in request.headers:
            ip = request.headers.get('X-Forwarded-For', 'localhost')
            if ip == 'localhost' and hasattr(request, 'remote_addr'):
                ip = request.remote_addr
            print(f"IP: {ip}")
            # Replace the API URL with the new IP
            provider.api_url = HttpUrl(str(provider.api_url).replace("localhost", ip))
            print(f"New API URL: {provider.api_url}")
    print(f"ProviderModel: {provider}")
    return await Provider.save_provider_in_db(
        access_token=user['session_id'],
        provider=provider,
        user_id=user['sub']
    )

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

# Model endpoints
@app.post('/models')
@error_handler
async def create_model(model: dict, user = Depends(authenticate)):
    print(f"Model: {model}")
    print(f"User: {user}")
    model_obj = LLM.from_dict(model)
    return await LLM.save_model_in_db(access_token=user['session_id'], user_id=user['sub'], model=model_obj)

@app.get('/models')
@error_handler
async def get_models(limit: int = 10, created_at_lt: datetime = datetime.now(), user = Depends(authenticate)):
    return await LLM.get_models(limit = limit, created_at_lt = created_at_lt)

@app.get('/models/{id}')
@error_handler
async def get_model(id: str, user = Depends(authenticate)):
    return await LLM.get_model(access_token=user['session_id'], id=id)

@app.get('/models/')
@error_handler
async def get_model_by_name(name: str, user = Depends(authenticate)):
    return await LLM.get_model(access_token=user['session_id'], user_id=user['sub'], name=name)

@app.put('/models/{id}')
@error_handler
async def update_model(id: str, model: dict, user = Depends(authenticate)):
    return await LLM.update_model(id, model)

@app.delete('/models/{id}')
@error_handler
async def delete_model(id: str, user = Depends(authenticate)):
    return await LLM.delete_model(id)

# Agents endpoints
@app.post('/agents')
@error_handler
async def create_agent(agent: AgentModel, user = Depends(authenticate)):
    agent_id = Agent.create_in_db(user['session_id'], agent)
    return agent_id

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
        
# Chat
@app.get("/instances/{id}/chat")
async def chat(id: str, message: dict = Body(..., media_type="application/json"), user = Depends(authenticate)):
    instance_model = Instance.get_in_db(str(id))
    instance = Instance(**instance_model.to_dict())
    res = await instance.chat_w_fn_calls(message["input"], access_token=user['session_id'], user_id=user['sub'])
    return res


@app.get("/instances/{id}/stream")
async def multiple_function_calls(id: str, input: str = Body(..., embed=True), user = Depends(authenticate)):
    print(f"ID: {id}")
    print(f"Input: {input}")
    instance_model = Instance.get_in_db(str(id))
    instance = Instance(**instance_model.to_dict())
    return StreamingResponse(instance.use_custom_library_async(input=input, access_token=user['session_id']), media_type="text/plain")

# Yaml parsing
@app.post('/yaml')
@error_handler
async def create_from_yaml(request: Request, user = Depends(authenticate)):
    try:
        fyodorov_yaml = await request.body()
        print(f"fyodorov_yaml: \n{fyodorov_yaml}")
        fyodorov_config = yaml.safe_load(fyodorov_yaml)
        print(f"fyodorov_config: \n{fyodorov_config}")
        response = {
            "providers": [],
            "models": [],
            "agents": [],
            "instances": [],
            "tools": []
        }
        print(f"fyodorov_config: \n{fyodorov_config}")
        if "providers" in fyodorov_config:
            print("Saving providers")
            for provider_dict in fyodorov_config["providers"]:
                print(f"Provider: {provider_dict}")
                provider = ProviderModel.from_dict(provider_dict)
                new_provider = await Provider.save_provider_in_db(user['session_id'], provider, user['sub'])
                response["providers"].append(new_provider)
        print("Saved providers", response["providers"])
        if "models" in fyodorov_config:
            for model_dict in fyodorov_config["models"]:
                model = LLMModel.from_dict(model_dict)
                print(f"Model: {model}")
                new_model = await LLM.save_model_in_db(user['session_id'], user['sub'], model)
                response["models"].append(new_model)
        print("Saved models", response["models"])
        if 'tools' in fyodorov_config:
            for tool_dict in fyodorov_config["tools"]:
                # marshall back to yaml
                tool_yaml = yaml.dump(tool_dict)
                print(f"Tool: {tool_yaml}")
                new_tool = ToolModel.from_yaml(tool_yaml)
                response["tools"].append(new_tool)
        print("Saved tools", response["tools"])
        if "agents" in fyodorov_config:
            for agent_dict in fyodorov_config["agents"]:
                new_agent = await Agent.save_from_dict(user['session_id'], user['sub'], agent_dict)
                response["agents"].append(new_agent)
        print("Saved agents", response["agents"])
        if len(response["agents"]) > 0:
            for agent in response["agents"]:
                instance = InstanceModel(agent_id=str(agent['id']), title="Default Instance")
                new_instance = Instance.create_in_db(user['session_id'], instance)
                response["instances"].append(new_instance)
        print("Saved instances", response["instances"])
        return response
    except Exception as e:
        print('Error parsing config from yaml', str(e))
        raise HTTPException(status_code=400, detail="Invalid YAML format")

# User endpoints
from fyodorov_utils.auth.endpoints import users_app
app.mount('/users', users_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
