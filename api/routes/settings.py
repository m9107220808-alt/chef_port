from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict

from api.database import get_db
from api.models.settings import ShopSettings
from api.schemas.settings import SettingSchema, SettingsUpdate

router = APIRouter()

@router.get("/", response_model=List[SettingSchema])
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Получить все настройки магазина"""
    result = await db.execute(select(ShopSettings))
    return result.scalars().all()

@router.get("/map", response_model=Dict[str, str])
async def get_settings_map(db: AsyncSession = Depends(get_db)):
    """Получить настройки в виде словаря key-value"""
    result = await db.execute(select(ShopSettings))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}

@router.post("/")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Обновить настройки магазина"""
    for key, value in data.settings.items():
        result = await db.execute(select(ShopSettings).where(ShopSettings.key == key))
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            new_setting = ShopSettings(key=key, value=value)
            db.add(new_setting)
    
    await db.commit()
    return {"status": "ok"}
