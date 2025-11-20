from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=5)
    address: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2)
    contacts: str = Field(..., min_length=5)

class PlaceCreate(PlaceBase):
    photos: List[str] = Field(default_factory=list)

class PlaceRead(PlaceBase):
    id: int
    photos: List[str]
    average_rating: float
    review_count: int
    created_at: datetime
    updated_at: datetime

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1)

class ReviewCreate(ReviewBase):
    place_id: int

class ReviewRead(ReviewBase):
    id: int
    user_id: int
    place_id: int
    user_username: str
    created_at: datetime
    
class CityList(BaseModel):
    cities: List[str]