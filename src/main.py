import yaml
from fastapi import FastAPI, Depends, HTTPException, Body, WebSocket, Request
from fastapi.responses import StreamingResponse

from datetime import datetime
from pydantic import HttpUrl
import uvicorn

from fyodorov_utils.auth.auth import authenticate
from fyodorov_utils.decorators.logging import error_handler
from fyodorov_utils.services.yaml import app as yaml_app

from fyodorov_llm_agents.instances.instance_service import Instance
from fyodorov_llm_agents.instances.instance_model import InstanceModel
from fyodorov_llm_agents.agents.agent_model import Agent as AgentModel
from fyodorov_llm_agents.tools.mcp_tool_model import MCPTool as ToolModel
from fyodorov_llm_agents.providers.provider_service import Provider
from fyodorov_llm_agents.providers.provider_model import ProviderModel
from fyodorov_llm_agents.agents.agent_service import AgentService as Agent
from fyodorov_llm_agents.models.llm_service import LLMService
from fyodorov_llm_agents.models.llm_model import LLMModel

# User endpoints
from fyodorov_utils.auth.endpoints import users_app

app = FastAPI(
    title="Gagarin",
    description="A service for creating and managing chatbots and agents",
    version="0.0.1",
)
app.mount("/users", users_app)
app.mount("/yaml", yaml_app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request here
    print(f"Request: {request.method} {request.url}")
    print(f"Headers: {request.headers}")
    print(f"Body: {await request.body()}")

    response = await call_next(request)

    return response


# Gagarin API
@app.get("/")
@error_handler
def root():
    return "Gagarin API v1"


@app.get("/health")
@error_handler
def health_check():
    return "OK"


# Providers endpoints
@app.post("/providers")
@error_handler
async def create_provider(
    provider_model: ProviderModel, request: Request, user=Depends(authenticate)
):
    print(f"User: {user}")
    if "localhost" in str(provider_model.api_url):
        print("Replacing IP in API URL")
        # Get the IP address of the user
        print(f"Request: {request.headers}")
        if "X-Forwarded-For" in request.headers:
            ip = request.headers.get("X-Forwarded-For", "localhost")
            if ip == "localhost" and hasattr(request, "remote_addr"):
                ip = request.remote_addr
            print(f"IP: {ip}")
            # Replace the API URL with the new IP
            provider_model.api_url = HttpUrl(str(provider_model.api_url).replace("localhost", ip))
            print(f"New API URL: {provider_model.api_url}")
    print(f"ProviderModel: {provider_model}")
    provider = Provider(user_id=user["sub"], access_token=user["session_id"])
    return await provider.upsert_in_db(
        model=provider_model, access_token=user["session_id"], user_id=user["sub"]
    )


@app.get("/providers")
@error_handler
async def get_providers(
    limit: int = 10,
    created_at_lt: datetime = datetime.now(),
    user=Depends(authenticate),
):
    provider = Provider(user_id=user["sub"], access_token=user["session_id"])
    return await provider.get_providers(limit=limit, created_at_lt=created_at_lt)


@app.get("/providers/{id}")
@error_handler
async def get_provider(id: str, user=Depends(authenticate)):
    provider = Provider(user_id=user["sub"], access_token=user["session_id"])
    provider_model = await provider.get_provider_by_id(id)
    if not provider_model:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider_model


@app.put("/providers/{id}")
@error_handler
async def update_provider(id: str, provider: dict, user=Depends(authenticate)):
    provider = Provider(user_id=user["sub"], access_token=user["session_id"])
    return await provider.update_provider_in_db(id, update=provider)


@app.delete("/providers/{id}")
@error_handler
async def delete_provider(id: str, user=Depends(authenticate)):
    provider = Provider(user_id=user["sub"], access_token=user["session_id"])
    return await provider.delete_provider_in_db(id)


# Model endpoints
@app.post("/models")
@error_handler
async def create_model(model: dict, user=Depends(authenticate)):
    model_obj = LLMModel.from_dict(model)
    llm_service = LLMService(access_token=user["session_id"])
    result = await llm_service.save_model_in_db(
        access_token=user["session_id"], user_id=user["sub"], model=model_obj
    )
    return result


@app.get("/models")
@error_handler
async def get_models(
    limit: int = 10,
    created_at_lt: datetime = datetime.now(),
    user=Depends(authenticate),
):
    llm_service = LLMService()
    return await llm_service.get_models(
        access_token=user["session_id"],
        user_id=user["sub"],
        limit=limit,
        created_at_lt=created_at_lt
    )


@app.get("/models/{id}")
@error_handler
async def get_model(id: str, user=Depends(authenticate)):
    llm_service = LLMService()
    return await llm_service.get_model(access_token=user["session_id"], id=id)


@app.get("/models/")
@error_handler
async def get_model_by_name(name: str, user=Depends(authenticate)):
    llm_service = LLMService()
    return await llm_service.get_model(
        access_token=user["session_id"], user_id=user["sub"], name=name
    )


@app.put("/models/{id}")
@error_handler
async def update_model(id: str, model: dict, user=Depends(authenticate)):
    llm_service = LLMService()
    return await llm_service.update_model_by_id_in_db(
        access_token=user["session_id"], id=id, update_data=model
    )


@app.delete("/models/{id}")
@error_handler
async def delete_model(id: str, user=Depends(authenticate)):
    llm_service = LLMService()
    return await llm_service.delete_model_in_db(access_token=user["session_id"], id=id)


# Agents endpoints
@app.post("/agents")
@error_handler
async def create_agent(agent: AgentModel, user=Depends(authenticate)):
    print("got request to create agent")
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    print("created agent service")
    agent_id = await agent_service.create_in_db(agent)
    print("created agent")
    return agent_id


@app.post("/agents/yaml")
@error_handler
async def create_agent_from_yaml(request: Request, user=Depends(authenticate)):
    try:
        body = await request.body()
        body_yaml = yaml.safe_load(body)
        agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
        if 'agents' in body_yaml:
            for agent_yaml in body_yaml['agents']:
                agent_model = AgentModel.from_yaml(agent_yaml)
                return await agent_service.create_in_db(agent_model, access_token=user["session_id"])
        else:
            agent_model = AgentModel.from_yaml(body_yaml)
            return await agent_service.create_in_db(agent_model, access_token=user["session_id"], )
    except Exception as e:
        print("Error creating agent from yaml", str(e))
        raise HTTPException(status_code=400, detail="Invalid YAML format")


@app.get("/agents")
@error_handler
async def get_agents(
    user=Depends(authenticate),
    limit: int = 10,
    created_at_lt: datetime = datetime.now(),
):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    agents = await agent_service.get_all_in_db(limit=limit, created_at_lt=created_at_lt)
    if not agents:
        raise HTTPException(status_code=404, detail="No agents found")
    return agents


@app.get("/agents/{id}")
@error_handler
async def get_agent(id: str, user=Depends(authenticate)):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    agent_model = await agent_service.get_in_db(id)
    if not agent_model:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_model


@app.put("/agents/{id}")
@error_handler
async def update_agent(id: str, agent: dict, user=Depends(authenticate)):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    return await agent_service.update_in_db(id, agent)


@app.delete("/agents/{id}")
@error_handler
async def delete_agent(id: str, user=Depends(authenticate)):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    return await agent_service.delete_in_db(id)


@app.get("/agents/{id}/tools")
@error_handler
async def get_agent_tools(id: str, user=Depends(authenticate)):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    return await agent_service.get_agent_tools(user["session_id"], id)


@app.post("/agents/{id}/tools")
@error_handler
async def assign_agent_tools(
    id: str, tools: list[ToolModel], user=Depends(authenticate)
):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    return await agent_service.assign_agent_tools(user["session_id"], id, tools)


@app.delete("/agents/{id}/tools/{tool_id}")
@error_handler
async def remove_agent_tool(id: str, tool_id: str, user=Depends(authenticate)):
    agent_service = Agent(user_id=user["sub"], access_token=user["session_id"])
    return await agent_service.delete_agent_tool_connection(user["session_id"], id, tool_id)


# Instances endpoints
@app.post("/instances")
@error_handler
async def create_instance(instance: InstanceModel, user=Depends(authenticate)):
    agent = await Agent.get_in_db(id=instance.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    instance = await Instance.create_in_db(instance)
    return instance


@app.get("/instances")
@error_handler
async def get_instances(
    user=Depends(authenticate),
    limit: int = 10,
    created_at_lt: datetime = datetime.now(),
):
    return await Instance.get_all_in_db(limit=limit, created_at_lt=created_at_lt)


@app.get("/instances/{id}")
@error_handler
async def get_instance(id: str, user=Depends(authenticate)):
    return await Instance.get_in_db(id)


@app.put("/instances/{id}")
@error_handler
async def update_instance(id: str, instance: dict, user=Depends(authenticate)):
    return await Instance.update_in_db(id, instance)


@app.delete("/instances/{id}")
@error_handler
async def delete_instance(id: str, user=Depends(authenticate)):
    return await Instance.delete_in_db(id)


# Chat via websocket
# host a websocket where users can send and receive messages from an instance
@app.websocket("/instances/{id}/ws")
async def websocket_endpoint(id: str, websocket: WebSocket):
    await websocket.accept()
    instance_model = Instance.get_in_db(id)
    instance = Instance(**instance_model.to_dict())
    await websocket.send_text(
        [
            f"{tuple_item[0]}:\t {tuple_item[1]}\n"
            for tuple_item in instance.get_chat_history()
        ]
    )
    while True:
        data = await websocket.receive_text()
        # Process the received message
        # ...
        model_output = await instance.use_custom_library(data)
        await websocket.send_text(model_output)

# Chat
@app.get("/instances/{id}/chat")
async def chat(
    id: str,
    message: dict = Body(..., media_type="application/json"),
    user=Depends(authenticate),
):
    instance_model = await Instance.get_in_db(id)
    instance = Instance(**instance_model.to_dict())
    res = await instance.chat_w_fn_calls(
        message["input"], access_token=user["session_id"], user_id=user["sub"]
    )
    return res

@app.get("/instances/{id}/stream")
async def multiple_function_calls(
    id: str, input: str = Body(..., embed=True), user=Depends(authenticate)
):
    print(f"ID: {id}")
    print(f"Input: {input}")
    instance_model = await Instance.get_in_db(id)
    instance = Instance(**instance_model.to_dict())
    return StreamingResponse(
        instance.use_custom_library_async(input=input, access_token=user["session_id"]),
        media_type="text/plain",
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
