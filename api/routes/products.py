from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from api.database import get_db
from api.models.product import Product
from api.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 2000,
    category: str = None,
    in_stock: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список товаров с фильтрацией"""
    query = select(Product)
    
    if category:
        query = query.where(Product.category == category)
    if in_stock is not None:
        query = query.where(Product.in_stock == in_stock)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Получить один товар по ID"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return product

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый товар"""
    if not product.code:
        product.code = str(uuid.uuid4())[:8]
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    return db_product

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить товар"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    print(f"DEBUG UPDATE: id={product_id}, found={db_product}")
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Обновляем только переданные поля
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    await db.commit()
    await db.refresh(db_product)
    
    return db_product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_put(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить товар (PUT для совместимости с miniapp_admin)"""
    return await update_product(product_id, product_update, db)

@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить товар (мягкое удаление/hard delete)"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    print(f"DEBUG UPDATE: id={product_id}, found={db_product}")
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Hard delete for simplicity now, or soft delete if model supports it
    await db.delete(db_product) 
    await db.commit()
    
    return None
