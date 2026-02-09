from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    code: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0
    # v1.5 field
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    # v1.5 field
    image_url: Optional[str] = None

class CategoryResponse(CategoryBase):
    """Схема ответа категории"""
    id: int
    
    class Config:
        from_attributes = True
