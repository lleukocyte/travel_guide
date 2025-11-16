from typing import Annotated
from fastapi import APIRouter, HTTPException
from backend.users_crud import UserCrud
from backend.security import create_jwt_token, verify_password
from backend.users_schemas import UserCreate, UserRead
from backend.database import new_session

user_router = APIRouter()

def get_db():
    db = new_session()
    try:
        yield db
    finally:
        db.close()

@user_router.post("/register/")#, response_model=UserRead)
async def register(data: UserCreate):
    try:
        user = await UserCrud.create_user(data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=ve)
    return {"email": user.email, "username": user.username}

@user_router.post("/login/")
async def login(data: UserRead):
    user = await UserCrud.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(user.password_hash, data.password):
        raise HTTPException(status_code=403, detail="Invalid credentials")
    token = create_jwt_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}