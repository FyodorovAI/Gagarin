import jwt
import datetime

def create_jwt(payload: dict, secret: str):
    # Set the expiration time for the JWT
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 1 day validity
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token
