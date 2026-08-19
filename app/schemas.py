from pydantic import BaseModel, HttpUrl
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

    class Config:
        from_attributes = True

class PriceHistoryOut(BaseModel):
    id: int
    product_id: int
    price: float
    currency: str
    scraped_at: datetime
