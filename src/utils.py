from functools import wraps
from fastapi import HTTPException

def error_handler(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPException as http_exc:
            # Print the HTTPException with the function name and re-raise it
            print(f"{f.__name__} - HTTP Exception: {http_exc.detail}")
            raise
        except Exception as exc:
            # Print the exception with the function name and raise a generic HTTP 400 error
            print(f"{f.__name__} - Unhandled Exception: {exc}")
            raise HTTPException(status_code=400, detail="A generic error occurred")
    return wrapper

# Usage example
# @app.get("/items/{item_id}")
# @error_handler  # Apply the decorator directly
# async def read_item(item_id: int):
#     # Your endpoint logic here
#     pass
