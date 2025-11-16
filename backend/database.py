from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Integer, Float, JSON
from typing import Optional, List
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "app.db")
DB_URL = f"sqlite+aiosqlite:///./{DB_NAME}"

engine = create_async_engine(DB_URL, echo=True)
new_session = async_sessionmaker(engine, expire_on_commit=False)

class Model(DeclarativeBase):
    pass

class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

class Place(Model):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(50))
    contacts: Mapped[str] = mapped_column(String(200))
    photos: Mapped[str] = mapped_column(JSON, default=list)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="place")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="place")

    def __repr__(self):
        return f"<Place(id={self.id}, name={self.name}, city={self.city})>"

class Review(Model):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    comment: Mapped[str] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    place: Mapped["Place"] = relationship("Place", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, place_id={self.place_id}, user_id={self.user_id}, rating={self.rating})>"

class Favorite(Model):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    place: Mapped["Place"] = relationship("Place", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, place_id={self.place_id})>"

async def create_tables():
    """Создание всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    print("✅ Все таблицы созданы/проверены")

async def delete_tables():
    """Удаление таблиц (только для тестов!)"""
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
    print("🗑️ Таблицы удалены")