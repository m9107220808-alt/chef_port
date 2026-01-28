from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    id: int  # Telegram ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = None

class UserResponse(BaseModel):
    """Схема ответа пользователя"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
