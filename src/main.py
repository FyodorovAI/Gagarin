from fastapi import FastAPI, Depends, HTTPException, Security, Body, WebSocket
from pydantic import BaseModel, EmailStr
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_403_FORBIDDEN
from datetime import datetime
import jwt
from typing import List
import uvicorn

from services.agent import Agent
from services.instance import Instance
from services.provider import Provider
from models.agent import AgentModel
from models.instance import InstanceModel
from models.provider import ProviderModel
from config.supabase import get_supabase
from config.config import Settings
from utils import error_handler  # Import the decorator from utils.py

app = FastAPI()
supabase = get_supabase()
settings = Settings()
security = HTTPBearer()

async def authenticate(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        # Perform additional validation checks as needed (e.g., expiration, issuer, audience)
        return payload  # Or a user object based on the payload
    except jwt.PyJWTError as e:
        print(f"JWT error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        ) from e


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
def create_provider(provider: ProviderModel, user = Depends(authenticate)):
    Provider.create_in_db(provider)
    return provider

@app.get('/providers')
@error_handler
def get_providers(user = Depends(authenticate), limit: int = 10, created_at_lt: datetime = datetime.now()):
    return Provider.get_providers(limit = limit, created_at_lt = created_at_lt)

@app.get('/providers/{id}')
@error_handler
def get_provider(id: str, user = Depends(authenticate)):
    return Provider.get_provider_by_id(id)

@app.put('/providers/{id}')
@error_handler
def update_provider(id: str, provider: ProviderModel, user = Depends(authenticate)):
    return Provider.update_provider_in_db(id, provider)

@app.delete('/providers/{id}')
@error_handler
def delete_provider(id: str, user = Depends(authenticate)):
    return Provider.delete_provider_in_db(id)

# Agents endpoints
@app.post('/agents')
@error_handler
def create_agent(agent: AgentModel, user = Depends(authenticate)):
    Agent.create_in_db(agent)
    return agent

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
def update_agent(id: str, agent: AgentModel, user = Depends(authenticate)):
    return Agent.update_in_db(id, agent)

@app.delete('/agents/{id}')
@error_handler
def delete_agent(id: str, user = Depends(authenticate)):
    return Agent.delete_in_db(id)

# Instances endpoints
@app.post('/instances')
@error_handler
def create_instance(instance: InstanceModel, user = Depends(authenticate)):
    if instance.agent not in [agent.id for agent in Agent.get_all_in_db()]:
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
def update_instance(id: str, instance: InstanceModel, user = Depends(authenticate)):
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
    instance = Instance.get_in_db(id)
    await websocket.send_text("Hello, World!")
    while True:
        data = await websocket.receive_text()
        # Process the received message
        # ...
        instance.run_model(data)
        await websocket.send_text("Response to: " + data)

# User endpoints
@app.post('/users/sign_up')
@error_handler
async def sign_up(email: str = Body(...), password: str = Body(...), invite_code: str = Body(...)):
    print("About to sign up")
    print(f"Signing up using supabase: {supabase}")
    # Check if invite code exists
    invite_code_check = supabase.from_("invite_codes").select("nr_uses, max_uses").eq("code", invite_code).execute()
    if not invite_code_check.data:
        raise HTTPException(status_code=401, detail="Invalid invite code")

    invite_code_data = invite_code_check.data[0]
    nr_uses = invite_code_data['nr_uses']
    max_uses = invite_code_data['max_uses']

    if nr_uses >= max_uses:
        raise HTTPException(status_code=401, detail="Invite code has reached maximum usage")

    user = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {
                "invite_code": invite_code,
            }
        }
    })
    # Increment nr_uses in invite_codes table
    nr_uses += 1
    supabase.from_("invite_codes").update({"nr_uses": nr_uses}).eq("code", invite_code).execute()

    return {"message": "User created successfully", "jwt": user.session.access_token}

@app.post('/users/sign_in')
@error_handler
async def sign_in(email: str = Body(...), password: str = Body(...)):
    user = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    return {"message": "User signed in successfully", "jwt": user.session.access_token}


@app.post('/users/create_api_key')
@error_handler
async def create_api_key(expiration: int = 3600, user = Depends(authenticate)):
    api_key = supabase.auth.api_key_create()
    return {"message": "API key created successfully", "api_key": api_key}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
