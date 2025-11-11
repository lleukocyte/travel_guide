from typing import Annotated
from fastapi import APIRouter, Depends
from backend.crud import UserCrud
from backend.security import create_jwt_token, verify_password
from backend.schemas import UserCreate, UserRead, VerifyCode
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

@user_router.post("/verify/")
async def verify_email(data: VerifyCode):
    success = await UserCrud.activate_user(data)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid code")
    return {"message": "User activated"}

@user_router.post("/login/")
async def login(data: UserRead):
    user = await UserCrud.get_user_by_email(data.email)
    if not user or not verify_password(user.password_hash, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User not activated")
    token = create_jwt_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}