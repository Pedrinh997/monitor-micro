from pydantic import BaseModel, HttpUrl, EmailStr
from datetime import datetime
from typing import Optional

class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapeResponse(BaseModel):
    title: str
    price: float
    currency: str
    url: str

class ProductCreate(BaseModel):
    url: str
    target_price: Optional[float] = None

class ProductOut(BaseModel):
    id: int
    url: str
    title: Optional[str]
    target_price: Optional[float]
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class PriceHistoryOut(BaseModel):
    id: int
    product_id: int
    price: float
    currency: str
    scraped_at: datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
