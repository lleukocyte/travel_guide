from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.database import User, new_session
from backend.users_schemas import UserCreate
from backend.security import hash_password

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