from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from backend.users_crud import UserCrud
from backend.security import create_jwt_token, verify_password
from backend.users_schemas import UserCreate, UserRead
from backend.database import new_session, User
from backend.dependencies import get_current_user

user_router = APIRouter()

def get_db():
    db = new_session()
    try:
        yield db
    finally:
        db.close()

@user_router.post("/register/")
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

@user_router.post("/favorites/{place_id}")
async def add_favorite(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        user = await UserCrud.add_favorite_place(current_user.id, place_id)
        return {"message": "Место добавлено в избранное"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@user_router.delete("/favorites/{place_id}")
async def remove_favorite(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        user = await UserCrud.remove_favorite_place(current_user.id, place_id)
        return {"message": "Место удалено из избранного"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@user_router.get("/favorites")
async def get_favorites(current_user: User = Depends(get_current_user)):
    favorite_place_ids = await UserCrud.get_favorite_places(current_user.id)
    
    from backend.places_crud import PlaceCrud
    from backend.places_router import serialize_place
    
    places = []
    for place_id in favorite_place_ids:
        place = await PlaceCrud.get_place_by_id(place_id)
        if place:
            place_data = serialize_place(place)
            places = places + [place_data]
    
    return places

@user_router.get("/favorites/{place_id}/status")
async def get_favorite_status(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    is_favorite = await UserCrud.is_favorite_place(current_user.id, place_id)
    return {"is_favorite": is_favorite}