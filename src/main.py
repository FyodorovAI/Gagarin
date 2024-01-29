from fastapi import FastAPI, Depends, HTTPException, Security, Body, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_403_FORBIDDEN
from datetime import datetime
import jwt
from typing import List
import uvicorn

from services.tool import Tool
from services.health_check import HealthUpdate
from models.tool import ToolModel
from models.health_check import HealthUpdateModel
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

# Agents endpoints
@app.post('/agents')
@error_handler
def create_tool(tool: ToolModel, user = Depends(authenticate)):
    Tool.create_in_db(tool)
    return tool

@app.get('/agents')
@error_handler
def get_tools(user = Depends(authenticate), limit: int = 10, created_at_lt: datetime = datetime.now()):    
    return Tool.get_all_in_db(limit = limit, created_at_lt = created_at_lt)

@app.get('/agents/{id}')
@error_handler
def get_tool(id: str, user = Depends(authenticate)):
    return Tool.get_in_db(id)

@app.put('/agents/{id}')
@error_handler
def update_tool(id: str, tool: ToolModel, user = Depends(authenticate)):
    return Tool.update_in_db(id, tool)

@app.delete('/agents/{id}')
@error_handler
def delete_tool(id: str, user = Depends(authenticate)):
    return Tool.delete_in_db(id)

# User endpoints
@app.post('/users/sign_up')
@error_handler
async def sign_up(email: str = Body(...), password: str = Body(...), invite_code: str = Body(...)):
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
