from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from backend.database import new_session, User, Place, Review
from backend.places_schemas import PlaceCreate, ReviewCreate
from backend.geocoder import geocoder
import json
from typing import List, Optional, Dict
import asyncio
import re
from collections import defaultdict, Counter
import math
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

class PlaceCrud:
    _stemmer = SnowballStemmer("russian")
    _stop_words = set(stopwords.words("russian"))

    @classmethod
    async def create_place(cls, data: PlaceCreate, user_id: int) -> Place:
        async with new_session() as session:
            try:
                place_dict = data.model_dump()
                place_dict["photos"] = json.dumps(place_dict["photos"])
                
                coordinates = await geocoder.geocode_address(data.city, data.address)
                if coordinates:
                    place_dict["latitude"] = float(coordinates[0])
                    place_dict["longitude"] = float(coordinates[1])
                    print(f"Координаты {data.name}: {place_dict['latitude']}, {place_dict['longitude']}")
                else:
                    print(f"Не удалось получить координаты для: {data.name}")
                
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
    def _extract_tokens(cls, text: str) -> List[str]:
        text = text.lower()

        words = re.findall(r"[а-яёa-z]{3,}", text)

        tokens = [
            cls._stemmer.stem(word)
            for word in words
            if word not in cls._stop_words
        ]

        return list(set(tokens))
    
    @classmethod
    async def get_all_places(
        cls,
        city: Optional[str] = None,
        user: Optional[User] = None
    ) -> List[Place]:
        async with new_session() as session:

            query = select(Place)
            if city:
                query = query.where(Place.city == city)

            all_places = list((await session.execute(query)).scalars().all())

            if not user.favorite_places:
                return sorted(all_places, key=lambda p: p.average_rating, reverse=True)

            favorite_places = list((await session.execute(
                select(Place).where(Place.id.in_(user.favorite_places))
            )).scalars().all())

            if not favorite_places:
                return sorted(all_places, key=lambda p: p.average_rating, reverse=True)

            favorite_tokens = []
            for place in favorite_places:
                favorite_tokens.extend(
                    cls._extract_tokens(place.name + " " + place.description)
                )

            if not favorite_tokens:
                return sorted(all_places, key=lambda p: p.average_rating, reverse=True)

            tf = Counter(favorite_tokens)
            total_favorites = len(favorite_places)

            idf = {
                token: math.log(total_favorites / freq)
                for token, freq in tf.items()
            }

            scored_places = []

            for place in all_places:
                if place.id in user.favorite_places:
                    continue

                tokens = cls._extract_tokens(place.name + " " + place.description)

                score = sum(
                    tf[token] * idf[token]
                    for token in tokens
                    if token in idf
                )

                if score > 0:
                    scored_places.append((place, score))

            scored_places.sort(key=lambda x: x[1], reverse=True)

            recommended = [p for p, _ in scored_places]

            others = [
                p for p in all_places
                if p.id not in {pl.id for pl in recommended}
            ]
            others.sort(key=lambda p: p.average_rating, reverse=True)

            return recommended + others

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