from functools import wraps
from fastapi import HTTPException
import asyncio

def error_handler(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            # Use 'await' for async functions
            if asyncio.iscoroutinefunction(f):
                return await f(*args, **kwargs)
            else:
                return f(*args, **kwargs)
        except HTTPException as http_exc:
            print(f"{f.__name__} - HTTP Exception: {http_exc.detail}")
            raise
        except Exception as exc:
            print(f"{f.__name__} - Unhandled Exception: {exc}")
            raise HTTPException(status_code=400, detail="An error occurred")
    return wrapper

# Usage example
# @app.get("/items/{item_id}")
# @error_handler  # Apply the decorator directly
# async def read_item(item_id: int):
#     # Your endpoint logic here
#     pass
