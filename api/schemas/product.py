from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Базовая схема товара"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    weight: Optional[float] = Field(None, gt=0)
    unit: str = "шт"
    image_url: Optional[str] = None
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
    price: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    """Схема ответа товара"""
    id: int
    moysklad_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
