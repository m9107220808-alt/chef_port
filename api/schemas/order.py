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
    productcode: Optional[str] = None
    name: str
    quantity: float # Changed from int to float to match model
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
    userid: int = Field(..., alias="user_id") # Map model 'userid' to schema 'user_id'
    total: float = Field(..., alias="total_amount") # Map model 'total' to schema 'total_amount'
    status: str # Relaxed from OrderStatus enum to str to accept 'new'
    address: Optional[str] = Field(None, alias="delivery_address") # Map model 'address' to schema 'delivery_address'
    comment: Optional[str] = None
    paymenttype: Optional[str] = Field(None, alias="payment_method")
    paymentstatus: Optional[str] = Field(None, alias="payment_status")
    createdat: datetime = Field(..., alias="created_at")
    updatedat: Optional[datetime] = Field(None, alias="updated_at")
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True
        populate_by_name = True
