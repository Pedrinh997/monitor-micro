from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    target_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="BRL")
    scraped_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")
