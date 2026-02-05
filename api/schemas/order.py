from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    """Статусы заказа"""
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPING = "shipping"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemCreate(BaseModel):
    """Схема для создания позиции заказа"""
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemResponse(BaseModel):
    """Схема ответа позиции заказа"""
    id: int
    product_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """Схема для создания заказа"""
    user_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_method: str = "pickup"  # pickup или delivery
    delivery_address: Optional[str] = None
    payment_method: str = "cash"  # cash или card
    comment: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderResponse(BaseModel):
    """Схема ответа заказа"""
    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    delivery_address: str
    comment: Optional[str] = None
    payment_id: Optional[str] = None
    payment_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True
