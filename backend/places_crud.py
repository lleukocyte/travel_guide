from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from backend.database import new_session, User, Place, Review, Favorite
from backend.places_schemas import PlaceCreate, ReviewCreate
import json
from typing import List, Optional

class PlaceCrud:
    @classmethod
    async def create_place(cls, data: PlaceCreate, user_id: int) -> Place:
        async with new_session() as session:
            try:
                place_dict = data.model_dump()
                place_dict["photos"] = json.dumps(place_dict["photos"])
                
                place = Place(**place_dict)
                session.add(place)
                await session.commit()
                await session.refresh(place)
                return place
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def get_place_by_id(cls, place_id: int) -> Place | None:
        async with new_session() as session:
            query = select(Place).where(Place.id == place_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_all_places(cls, city: Optional[str] = None) -> List[Place]:
        async with new_session() as session:
            query = select(Place)
            if city:
                query = query.where(Place.city == city)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_cities(cls) -> List[str]:
        async with new_session() as session:
            query = select(Place.city).distinct()
            result = await session.execute(query)
            return [row[0] for row in result.all()]

class ReviewCrud:
    @classmethod
    async def create_review(cls, data: ReviewCreate, user_id: int) -> Review:
        async with new_session() as session:
            try:
                # Check if user already reviewed this place
                existing_review = await session.execute(
                    select(Review).where(
                        and_(Review.place_id == data.place_id, Review.user_id == user_id)
                    )
                )
                if existing_review.scalar_one_or_none():
                    raise ValueError("Вы уже оставили отзыв для этого места")

                review = Review(**data.model_dump(), user_id=user_id)
                session.add(review)
                await session.commit()
                await session.refresh(review)
                return review
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def get_reviews_by_place(cls, place_id: int) -> List[Review]:
        async with new_session() as session:
            query = select(Review).where(Review.place_id == place_id)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_user_by_id(cls, user_id: int) -> User | None:
        async with new_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

class FavoriteCrud:
    @classmethod
    async def add_favorite(cls, place_id: int, user_id: int) -> Favorite:
        async with new_session() as session:
            try:
                # Check if already favorited
                existing_fav = await session.execute(
                    select(Favorite).where(
                        and_(Favorite.place_id == place_id, Favorite.user_id == user_id)
                    )
                )
                if existing_fav.scalar_one_or_none():
                    raise ValueError("Место уже в избранном")

                favorite = Favorite(place_id=place_id, user_id=user_id)
                session.add(favorite)
                await session.commit()
                await session.refresh(favorite)
                return favorite
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def remove_favorite(cls, place_id: int, user_id: int) -> bool:
        async with new_session() as session:
            try:
                favorite = await session.execute(
                    select(Favorite).where(
                        and_(Favorite.place_id == place_id, Favorite.user_id == user_id)
                    )
                )
                favorite = favorite.scalar_one_or_none()
                
                if not favorite:
                    return False
                
                await session.delete(favorite)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def get_user_favorites(cls, user_id: int) -> List[Favorite]:
        async with new_session() as session:
            query = select(Favorite).where(Favorite.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def is_favorite(cls, place_id: int, user_id: int) -> bool:
        async with new_session() as session:
            query = select(Favorite).where(
                and_(Favorite.place_id == place_id, Favorite.user_id == user_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None