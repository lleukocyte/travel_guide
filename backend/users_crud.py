from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.database import User, new_session
from backend.users_schemas import UserCreate
from backend.security import hash_password
from typing import List

class UserCrud:
    @classmethod
    async def get_user_by_email(cls, email: str) -> User | None:
        async with new_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()
            
            if user_model:
                return user_model
            return None

    @classmethod
    async def create_user(cls, data: UserCreate) -> User:
        async with new_session() as session:
            existing_user = await cls.get_user_by_email(data.email)
            if existing_user:
                raise ValueError("Пользователь с этой почтой уже зарегистрирован.")

            try:               
                user_dict = data.model_dump()
                user_dict["password_hash"] = hash_password(user_dict.pop("password"))

                user = User(**user_dict)
                session.add(user)
                await session.flush()
                await session.commit()
                return user
                
            except IntegrityError:
                await session.rollback()
                raise ValueError("User creation failed due to database constraints")
            except Exception as e:
                await session.rollback()
                raise e
    @classmethod
    async def add_favorite_place(cls, user_id: int, place_id: int) -> User:
        async with new_session() as session:
            user = await cls.get_user_by_id(user_id)
            if place_id not in user.favorite_places:
                user.favorite_places.append(place_id)
                await session.commit()
            return user

    @classmethod
    async def remove_favorite_place(cls, user_id: int, place_id: int) -> User:
        async with new_session() as session:
            user = await cls.get_user_by_id(user_id)
            if place_id in user.favorite_places:
                user.favorite_places.remove(place_id)
                await session.commit()
            return user

    @classmethod
    async def get_favorite_places(cls, user_id: int) -> List[int]:
        user = await cls.get_user_by_id(user_id)
        return user.favorite_places
    
    @classmethod
    async def is_favorite_place(cls, user_id: int, place_id: int) -> bool:
        user = await cls.get_user_by_id(user_id)
        if not user:
            return False

        return place_id in user.favorite_places
