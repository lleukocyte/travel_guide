from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from backend.database import User, new_session
from backend.schemas import UserCreate, UserRead, VerifyCode
from backend.security import hash_password
import uuid
from backend.email_sender import send_code
import random
import string

def gen_verification_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length)).upper()

class UserCrud:
    @classmethod
    async def get_user_by_email(cls, email: str) -> User | None:
        async with new_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()
            
            if user_model:
                return User.model_validate(user_model)
            return None

    @classmethod
    async def create_user(cls, data: UserCreate) -> User:
        async with new_session() as session:
            existing_user = await cls.get_user_by_email(data.email)
            if existing_user:
                raise ValueError("Пользователь с этой почтой уже зарегистрирован.")

            try:
                verification_code = gen_verification_code()
                
                user_dict = data.model_dump()
                user_dict["password_hash"] = hash_password(user_dict.pop("password"))
                user_dict["verification_code"] = verification_code
                user_dict["is_active"] = False

                user = User(**user_dict)
                session.add(user)
                await session.flush()
                await session.commit()
                
                send_code(data.email, verification_code)
                
                return user
                
            except IntegrityError:
                await session.rollback()
                raise ValueError("User creation failed due to database constraints")
            except Exception as e:
                await session.rollback()
                raise e
            
    @classmethod
    async def activate_user(cls, verification: VerifyCode) -> bool:
        async with new_session() as session:
            query = select(User).where(User.email == verification.email)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                if user.verification_code == verification.code:
                    user.is_active = True
                    user.verification_code = None
                    await session.commit()
                    return True
            return False