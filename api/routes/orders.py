from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from api.database import get_db
from api.models.order import Order, OrderItem
from api.models.user import User
from api.models.product import Product
from api.schemas.order import OrderCreate, OrderResponse

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список заказов"""
    query = select(Order).options(selectinload(Order.items))
    
    if user_id:
        query = query.where(Order.user_id == user_id)
    
    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Получить один заказ по ID"""
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    return order

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый заказ"""
    
    # Проверяем товары и считаем сумму
    total_amount = 0.0
    order_items = []
    
    for item in order_data.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Товар {item.product_id} не найден")
        
        # Закомментируем проверку на наличие - товары всегда доступны для демо
        # if not product.in_stock:
        #     raise HTTPException(status_code=400, detail=f"Товар {product.name} нет в наличии")
        
        price = product.priceperkg if product.priceperkg else 0
        item_price = price * item.quantity
        total_amount += item_price
        
        order_items.append(OrderItem(
            productcode=product.code,
            name=product.name,
            quantity=item.quantity,
            price=price
        ))
    
    # Формируем адрес
    delivery_address = order_data.delivery_address or "Самовывоз"
    if order_data.delivery_method == "pickup":
        delivery_address = "Самовывоз"
    
    # Создаём заказ
    db_order = Order(
        userid=order_data.user_id,
        total=total_amount,
        address=delivery_address,
        deliverytype=order_data.delivery_method,
        paymenttype=order_data.payment_method,
        # comment=order_data.comment, # Комментарий пока некуда сохранять в модели
        items=order_items
    )
    
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    
    # Загружаем связи
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == db_order.id)
    )
    order = result.scalar_one()
    
    # Manually construct response to avoid Pydantic alias issues
    return OrderResponse(
        id=order.id,
        user_id=order.userid,
        total_amount=order.total,
        status=order.status,
        delivery_address=order.address,
        comment=None, # Поля comment нет в модели Order
        payment_method=order.paymenttype,
        payment_status=order.paymentstatus,
        created_at=order.createdat,
        updated_at=order.updatedat,
        items=[
            {
                "id": item.id,
                "productcode": item.productcode,
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price
            } for item in order.items
        ]
    )
