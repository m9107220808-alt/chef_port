from pydantic import BaseModel
from typing import Optional


class CategoryResponse(BaseModel):
    """Схема ответа категории"""
    id: int
    code: str
    name: str
    sort_order: Optional[int] = 0
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True
