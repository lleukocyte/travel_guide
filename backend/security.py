from argon2 import PasswordHasher
import jwt
import os
from datetime import datetime, timedelta

ph = PasswordHasher()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

PEPPER = os.getenv("PEPPER")

def hash_password(password: str) -> str:
    return ph.hash(password + PEPPER)

def verify_password(hashed: str, password: str) -> bool:
    try:
        ph.verify(hashed, password + PEPPER)
        return True
    except Exception:
        return False

def create_jwt_token(data: dict, expires_minutes=1440):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
    
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")