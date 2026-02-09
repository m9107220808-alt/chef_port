from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Базовая схема товара"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    cost_price: float = Field(default=0, ge=0)
    markup: int = Field(default=0, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    unit: str = "шт"
    category: Optional[str] = None
    in_stock: bool = True
    is_active: bool = True

class ProductCreate(ProductBase):
    """Схема для создания товара"""
    pass

class ProductUpdate(BaseModel):
    """Схема для обновления товара"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    markup: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    """Схема ответа товара"""
    id: int
    categoryid: Optional[int] = None
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    priceperkg: Optional[float] = None
    cost_price: Optional[float] = None
    markup: Optional[int] = None
    weight: Optional[float] = None
    is_weighted: Optional[bool] = False
    min_weight: Optional[float] = None
    is_hit: Optional[bool] = False
    is_discount: Optional[bool] = False
    discount_percent: Optional[int] = 0
    image_url: Optional[str] = None
    externalid: Optional[str] = None
    
    class Config:
        from_attributes = True
