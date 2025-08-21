from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    image = Column(String)
    type = Column(String)
    price = Column(Float)
    quantity = Column(Integer)

class CartItem(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float) 

class TrendingProduct(Base):
    __tablename__ = "trending_products"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    view_count = Column(Integer)
    updated_at = Column(String)  # ISO timestamp string, or use DateTime if preferred

class UserSuggestion(Base):
    __tablename__ = "user_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    product_id = Column(Integer, index=True)
    updated_at = Column(String)  # ISO timestamp string, or use DateTime if preferred 