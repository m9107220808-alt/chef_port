from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from api.database import get_db
from api.models.user import User
from api.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Получить список пользователей"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user

@router.post("/", response_model=UserResponse, status_code=201)
async def create_or_update_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать или обновить пользователя (upsert)"""
    result = await db.execute(select(User).where(User.id == user_data.id))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Обновляем существующего
        for field, value in user_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(existing_user, field, value)
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    else:
        # Создаём нового
        db_user = User(**user_data.model_dump())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Обновить данные пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    
    return db_user
