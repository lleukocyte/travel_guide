from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
import os
import uuid
import json
import asyncio

from backend.places_crud import PlaceCrud, ReviewCrud
from backend.users_crud import UserCrud
from backend.places_schemas import PlaceCreate, PlaceRead, ReviewCreate, ReviewRead, CityList
from backend.dependencies import get_current_user
from backend.database import User, new_session
from backend.geocoder import geocoder

places_router = APIRouter(prefix="/places", tags=["places"])
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def serialize_place(place) -> dict:
    photos = []
    
    try:
        if place.photos:
            if isinstance(place.photos, str):
                parsed = json.loads(place.photos)
                if isinstance(parsed, list):
                    photos = parsed
                else:
                    photos = [parsed]
            elif isinstance(place.photos, list):
                photos = place.photos
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing photos for place {place.id}: {e}")
        photos = []
    
    photos = [photo for photo in photos if photo]

    return {
        "id": place.id,
        "name": place.name,
        "description": place.description,
        "address": place.address,
        "city": place.city,
        "contacts": place.contacts,
        "photos": photos,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "average_rating": place.average_rating,
        "review_count": 0,
        "created_at": place.created_at,
        "updated_at": place.updated_at
    }

async def save_uploaded_files(files: List[UploadFile]) -> List[str]:
    photo_urls = []
    
    for file in files:
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        photo_urls.append(file_path)
    
    return photo_urls

@places_router.post("/", response_model=PlaceRead)
async def create_place(
    name: str = Form(...),
    description: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    contacts: str = Form(...),
    photos: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        photo_urls = await save_uploaded_files(photos)
        
        place_data = PlaceCreate(
            name=name,
            description=description,
            address=address,
            city=city,
            contacts=contacts,
            photos=photo_urls
        )
        
        place = await PlaceCrud.create_place(place_data, current_user.id)
        return serialize_place(place)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@places_router.get("/", response_model=List[PlaceRead])
async def get_places(city: Optional[str] = Query(None),
                     current_user: User = Depends(get_current_user)):
    places = await PlaceCrud.get_all_places(city=city, user=current_user)
    result = []
    for place in places:
        place_data = serialize_place(place)
        reviews = await ReviewCrud.get_reviews_by_place(place.id)
        place_data["review_count"] = len(reviews)
        place_data["average_rating"] = 0
        for rev in reviews:
            place_data["average_rating"] += rev.rating
        if len(reviews):
            place_data["average_rating"] /= len(reviews)
        result.append(place_data)
    return result

@places_router.get("/cities", response_model=CityList)
async def get_cities():
    cities = await PlaceCrud.get_cities()
    return {"cities": cities}

@places_router.get("/{place_id}", response_model=PlaceRead)
async def get_place(place_id: int):
    place = await PlaceCrud.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    place_data = serialize_place(place)
    reviews = await ReviewCrud.get_reviews_by_place(place_id)
    place_data["review_count"] = len(reviews)
    place_data["average_rating"] = 0
    for rev in reviews:
        place_data["average_rating"] += rev.rating
    if len(reviews):
        place_data["average_rating"] /= len(reviews)
    
    return place_data

@places_router.post("/{place_id}/reviews", response_model=ReviewRead)
async def create_review(
    place_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user)
):
    place = await PlaceCrud.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    try:
        review_data.place_id = place_id
        review = await ReviewCrud.create_review(review_data, current_user.id)
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "place_id": review.place_id,
            "rating": review.rating,
            "comment": review.comment,
            "user_username": current_user.username,
            "created_at": review.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@places_router.get("/{place_id}/reviews", response_model=List[ReviewRead])
async def get_place_reviews(place_id: int):
    reviews = await ReviewCrud.get_reviews_by_place(place_id)
    result = []
    for review in reviews:
        user = await UserCrud.get_user_by_id(review.user_id)
        result.append({
            "id": review.id,
            "user_id": review.user_id,
            "place_id": review.place_id,
            "rating": review.rating,
            "comment": review.comment,
            "user_username": user.username if user else "Unknown",
            "created_at": review.created_at
        })
    return result

@places_router.post("/geocode/address")
async def geocode_address(city: str = Form(...), address: str = Form(...)):
    try:
        coordinates = asyncio.run(geocoder.geocode_address(city, address))
        if coordinates:
            return {
                "success": True,
                "coordinates": coordinates,
                "message": f"Координаты найдены для {city}, {address}"
            }
        else:
            return {
                "success": False,
                "message": "Не удалось найти координаты для указанного адреса"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка геокодирования: {str(e)}")
    
@places_router.post("/{place_id}/geocode")
async def geocode_place(place_id: int):
    place = await PlaceCrud.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    coordinates = await PlaceCrud.update_place_coordinates(place_id)
    if coordinates:
        return {
            "success": True,
            "place_id": place_id,
            "coordinates": coordinates,
            "message": "Координаты обновлены"
        }
    else:
        return {
            "success": False,
            "message": "Не удалось получить координаты для этого адреса"
        }

@places_router.post("/{place_id}/coordinates")
async def save_place_coordinates(
    place_id: int,
    data: dict,
    current_user: User = Depends(get_current_user)
):
    place = await PlaceCrud.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    async with new_session() as session:
        place.latitude = data.get("latitude")
        place.longitude = data.get("longitude")
        await session.commit()
        await session.refresh(place)
        
        return {"success": True, "message": "Координаты сохранены"}