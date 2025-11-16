from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
import os
import uuid
import json

from backend.places_crud import PlaceCrud, ReviewCrud, FavoriteCrud
from backend.places_schemas import PlaceCreate, PlaceRead, ReviewCreate, ReviewRead, FavoriteRead, CityList
from backend.dependencies import get_current_user
from backend.database import User

places_router = APIRouter(prefix="/places", tags=["places"])
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def serialize_place(place) -> dict:
    photos = []
    
    try:
        if place.photos:
            # Пытаемся распарсить JSON
            if isinstance(place.photos, str):
                parsed = json.loads(place.photos)
                if isinstance(parsed, list):
                    photos = parsed
                else:
                    photos = [parsed]  # Если одна строка, делаем список
            elif isinstance(place.photos, list):
                photos = place.photos
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing photos for place {place.id}: {e}")
        photos = []
    
    # Фильтруем пустые значения
    photos = [photo for photo in photos if photo]
    
    return {
        "id": place.id,
        "name": place.name,
        "description": place.description,
        "address": place.address,
        "city": place.city,
        "contacts": place.contacts,
        "photos": photos,  # Гарантированно список
        "average_rating": place.average_rating,
        "review_count": 0,
        "created_at": place.created_at,
        "updated_at": place.updated_at
    }

async def save_uploaded_files(files: List[UploadFile]) -> List[str]:
    """Сохраняет загруженные файлы и возвращает список URL"""
    photo_urls = []
    
    for file in files:
        # Генерируем уникальное имя файла
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Сохраняем файл
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Сохраняем URL для доступа к файлу
        photo_urls.append(file_path)
    
    return photo_urls

@places_router.post("/", response_model=PlaceRead)
async def create_place(
    name: str = Form(...),
    description: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    contacts: str = Form(...),
    photos: List[UploadFile] = File(...),  # Принимаем несколько файлов
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
async def get_places(city: Optional[str] = Query(None)):
    places = await PlaceCrud.get_all_places(city=city)
    result = []
    for place in places:
        place_data = serialize_place(place)
        # Получаем количество отзывов
        reviews = await ReviewCrud.get_reviews_by_place(place.id)
        place_data["review_count"] = len(reviews)
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
        user = await ReviewCrud.get_user_by_id(review.user_id)
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

@places_router.post("/{place_id}/favorites")
async def add_to_favorites(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    place = await PlaceCrud.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    try:
        await FavoriteCrud.add_favorite(place_id, current_user.id)
        return {"message": "Место добавлено в избранное"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@places_router.delete("/{place_id}/favorites")
async def remove_from_favorites(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    success = await FavoriteCrud.remove_favorite(place_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Место не найдено в избранном")
    return {"message": "Место удалено из избранного"}

@places_router.get("/{place_id}/favorites/status")
async def get_favorite_status(
    place_id: int,
    current_user: User = Depends(get_current_user)
):
    is_fav = await FavoriteCrud.is_favorite(place_id, current_user.id)
    return {"is_favorite": is_fav}

@places_router.get("/user/favorites", response_model=List[FavoriteRead])
async def get_user_favorites(current_user: User = Depends(get_current_user)):
    favorites = await FavoriteCrud.get_user_favorites(current_user.id)
    
    result = []
    for favorite in favorites:
        place = await PlaceCrud.get_place_by_id(favorite.place_id)
        if place:
            place_data = serialize_place(place)
            reviews = await ReviewCrud.get_reviews_by_place(place.id)
            place_data["review_count"] = len(reviews)
            result.append({
                "id": favorite.id,
                "place_id": favorite.place_id,
                "place": place_data,
                "created_at": favorite.created_at
            })
    
    return result