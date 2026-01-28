"""
PostgreSQL Database Layer для Telegram Bot
Асинхронные функции для работы с БД через SQLAlchemy
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from api.database import Base
from api.models.category import Category
from api.models.product import Product
from api.models.cart import Cart
from api.models.order import Order, OrderItem
from api.models.order_history import OrderHistory
from api.models.user_profile import UserProfile
from api.models.user_address import UserAddress
from api.models.order_message import OrderMessage

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql+asyncpg://postgres:mA2kDs5jk@localhost:5432/chefport_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# ===== ИНИЦИАЛИЗАЦИЯ БД =====

async def create_tables():
    """Создать все таблицы в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Таблицы созданы")


async def init_demo_catalog():
    """Инициализация демо-каталога"""
    async with async_session() as session:
        result = await session.execute(select(func.count(Category.id)))
        count = result.scalar()

        if count > 0:
            logger.info("📦 Каталог уже инициализирован")
            return

        categories = [
            Category(code="fresh_fish", name="Свежая рыба", sortorder=1),
            Category(code="frozen", name="Замороженные продукты", sortorder=2),
            Category(code="smoked", name="Копчено-соленые", sortorder=3),
            Category(code="delicacy", name="Деликатесы", sortorder=4),
        ]

        session.add_all(categories)
        await session.flush()

        products = [
            Product(
                categoryid=categories[0].id,
                code="salmon",
                name="Филе Атлантического лосося",
                priceperkg=1780,
                isweighted=True,
                minweightkg=0.5,
                description="Свежее филе премиум качества"
            ),
            Product(
                categoryid=categories[0].id,
                code="seabass",
                name="Морской окунь",
                priceperkg=1300,
                isweighted=True,
                minweightkg=1.0,
                description="Цельная охлажденная рыба"
            ),
            Product(
                categoryid=categories[1].id,
                code="shrimp",
                name="Креветки королевские",
                priceperkg=2500,
                isweighted=True,
                minweightkg=0.5,
                description="Замороженные неочищенные"
            ),
        ]

        session.add_all(products)
        await session.commit()
        logger.info("✅ Демо-каталог инициализирован")


# ===== КАТЕГОРИИ =====

async def get_categories() -> List[tuple]:
    """Получить все категории"""
    async with async_session() as session:
        result = await session.execute(
            select(Category).order_by(Category.sortorder)
        )
        categories = result.scalars().all()
        return [(cat.id, cat.code, cat.name, cat.sortorder) for cat in categories]


# ===== ТОВАРЫ =====

async def get_products_by_category(cat_code: str) -> List[tuple]:
    """Получить товары категории"""
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .join(Category, Product.categoryid == Category.id)
            .where(Category.code == cat_code)
            .order_by(Product.name)
        )
        products = result.scalars().all()

        return [
            (p.id, p.categoryid, p.code, p.name, p.priceperkg, 
             p.isweighted, p.minweightkg, p.description)
            for p in products
        ]


async def get_product_by_code(code: str) -> Optional[tuple]:
    """Получить товар по коду"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.code == code)
        )
        product = result.scalar_one_or_none()

        if not product:
            return None

        return (
            product.id, product.categoryid, product.name, 
            product.priceperkg, product.isweighted, 
            product.minweightkg, product.description
        )


async def get_product_by_id(product_id: int) -> Optional[tuple]:
    """Получить товар по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            return None

        return (
            product.id, product.categoryid, product.code, product.name,
            product.priceperkg, product.isweighted, 
            product.minweightkg, product.description
        )


# ===== КОРЗИНА =====

async def add_to_cart_db(user_id: int, product_code: str, quantity: float):
    """Добавить товар в корзину"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(
                and_(Cart.userid == user_id, Cart.productcode == product_code)
            )
        )
        cart_item = result.scalar_one_or_none()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if new_qty <= 0:
                await session.delete(cart_item)
            else:
                cart_item.quantity = new_qty
        else:
            if quantity > 0:
                cart_item = Cart(
                    userid=user_id,
                    productcode=product_code,
                    quantity=quantity
                )
                session.add(cart_item)

        await session.commit()


async def get_cart_db(user_id: int) -> List[Dict[str, Any]]:
    """Получить корзину пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart, Product)
            .join(Product, Cart.productcode == Product.code)
            .where(Cart.userid == user_id)
        )
        items = result.all()

        return [
            {
                "product_code": cart.productcode,
                "name": product.name,
                "price": product.priceperkg,
                "quantity": cart.quantity,
            }
            for cart, product in items
        ]


async def clear_cart_db(user_id: int):
    """Очистить корзину пользователя"""
    async with async_session() as session:
        await session.execute(
            delete(Cart).where(Cart.userid == user_id)
        )
        await session.commit()


async def remove_item_from_cart_db(user_id: int, product_code: str):
    """Удалить товар из корзины"""
    async with async_session() as session:
        await session.execute(
            delete(Cart).where(
                and_(Cart.userid == user_id, Cart.productcode == product_code)
            )
        )
        await session.commit()


# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =====

async def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Получить профиль пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.userid == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        return {
            "full_name": profile.fullname,
            "phone": profile.phone,
            "city": profile.city,
            "street": profile.street,
            "house": profile.house,
            "flat": profile.flat,
            "entrance": profile.entrance,
            "floor": profile.floor,
            "delivery_type": profile.deliverytype,
        }


async def upsert_user_profile(user_id: int, profile_data: Dict[str, Any]):
    """Создать или обновить профиль пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.userid == user_id)
        )
        profile = result.scalar_one_or_none()

        now = datetime.now()

        if profile:
            for key, value in profile_data.items():
                # Преобразуем snake_case в camelCase
                db_key = key.replace('_', '')
                if hasattr(profile, db_key):
                    setattr(profile, db_key, value)
            profile.updatedat = now
        else:
            # Преобразуем ключи
            db_data = {}
            for key, value in profile_data.items():
                db_key = key.replace('_', '')
                db_data[db_key] = value
            
            profile = UserProfile(
                userid=user_id,
                createdat=now,
                updatedat=now,
                **db_data
            )
            session.add(profile)

        await session.commit()


async def save_user_profile(user_id: int, profile_data: Dict[str, Any]):
    """Сохранить профиль"""
    await upsert_user_profile(user_id, profile_data)

# ===== АДРЕСА =====

async def get_user_addresses(user_id: int) -> List[Dict[str, Any]]:
    """Получить все адреса пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(UserAddress)
            .where(UserAddress.userid == user_id)
            .order_by(UserAddress.isdefault.desc(), UserAddress.id.desc())
        )
        addresses = result.scalars().all()

        return [
            {
                "id": addr.id,
                "label": addr.label or "Адрес",
                "address": addr.address,
                "is_default": addr.isdefault,
            }
            for addr in addresses
        ]


async def add_user_address(
    user_id: int, 
    address: str, 
    label: Optional[str] = None, 
    is_default: bool = False
):
    """Добавить новый адрес"""
    async with async_session() as session:
        if is_default:
            await session.execute(
                update(UserAddress)
                .where(UserAddress.userid == user_id)
                .values(isdefault=False)
            )

        new_address = UserAddress(
            userid=user_id,
            label=label,
            address=address,
            isdefault=is_default
        )

        session.add(new_address)
        await session.commit()


async def delete_user_address(address_id: int, user_id: int):
    """Удалить адрес"""
    async with async_session() as session:
        await session.execute(
            delete(UserAddress).where(
                and_(UserAddress.id == address_id, UserAddress.userid == user_id)
            )
        )
        await session.commit()


async def set_default_address(address_id: int, user_id: int):
    """Установить адрес по умолчанию"""
    async with async_session() as session:
        await session.execute(
            update(UserAddress)
            .where(UserAddress.userid == user_id)
            .values(isdefault=False)
        )

        await session.execute(
            update(UserAddress)
            .where(and_(UserAddress.id == address_id, UserAddress.userid == user_id))
            .values(isdefault=True)
        )

        await session.commit()


async def get_default_address(user_id: int) -> Optional[Dict[str, Any]]:
    """Получить основной адрес"""
    async with async_session() as session:
        result = await session.execute(
            select(UserAddress)
            .where(and_(UserAddress.userid == user_id, UserAddress.isdefault == True))
            .limit(1)
        )
        address = result.scalar_one_or_none()

        if not address:
            return None

        return {
            "id": address.id,
            "label": address.label or "Адрес",
            "address": address.address,
        }


# ===== ЗАКАЗЫ =====

async def create_order_db(
    user_id: int,
    name: str,
    phone: str,
    address: str,
    delivery_type: str,
    items: List[Dict[str, Any]],
    total: int,
    payment_type: str = "cash_no_change",
) -> int:
    """Создание заказа"""
    async with async_session() as session:
        now = datetime.now()

        order = Order(
            userid=user_id,
            name=name,
            phone=phone,
            address=address,
            deliverytype=delivery_type,
            status="new",
            paymentstatus="not_paid",
            paymenttype=payment_type,
            total=total,
            createdat=now,
            updatedat=now
        )
        session.add(order)
        await session.flush()

        for item in items:
            order_item = OrderItem(
                orderid=order.id,
                productcode=item.get("code"),
                name=item["name"],
                quantity=item["quantity"],
                price=item["price"]
            )
            session.add(order_item)

        history = OrderHistory(
            orderid=order.id,
            status="new",
            paymentstatus="not_paid",
            changedat=now,
            changedby=user_id,
            comment="Создан заказ"
        )
        session.add(history)

        await session.commit()
        return order.id


async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """Получить заказы пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.userid == user_id)
            .order_by(Order.createdat.desc())
        )
        orders = result.scalars().all()

        return [
            {
                'order_number': f"#{order.id}",
                'customer_name': order.name,
                'total_amount': order.total,
                'status': order.status,
                'created_at': order.createdat.isoformat() if order.createdat else "",
            }
            for order in orders
        ]


async def get_orders_with_items(user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Получение заказов с товарами"""
    async with async_session() as session:
        query = select(Order).where(Order.userid == user_id).order_by(Order.id.desc())

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        orders = result.scalars().all()

        output = []
        for order in orders:
            # Получаем items отдельно
            items_result = await session.execute(
                select(OrderItem).where(OrderItem.orderid == order.id)
            )
            items = items_result.scalars().all()

            output.append({
                "id": order.id,
                "total": order.total,
                "status": order.status,
                "created_at": int(order.createdat.timestamp()) if order.createdat else 0,
                "items": [
                    {
                        "name": item.name,
                        "qty": item.quantity,
                        "price": item.price,
                    }
                    for item in items
                ]
            })

        return output


async def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """Получение полных данных заказа"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        # Получаем items
        items_result = await session.execute(
            select(OrderItem).where(OrderItem.orderid == order_id)
        )
        items = items_result.scalars().all()

        return {
            "order_id": order.id,
            "user_id": order.userid,
            "name": order.name,
            "phone": order.phone,
            "address": order.address,
            "delivery_type": order.deliverytype,
            "total": order.total,
            "status": order.status,
            "payment_type": order.paymenttype,
            "payment_status": order.paymentstatus,
            "created_at": int(order.createdat.timestamp()) if order.createdat else 0,
            "items": [
                {
                    "product_code": item.productcode,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price,
                }
                for item in items
            ]
        }


async def save_order_message(order_id: int, user_id: int, message_id: int):
    """Сохранение ID сообщения с заказом"""
    async with async_session() as session:
        await session.execute(
            delete(OrderMessage).where(OrderMessage.orderid == order_id)
        )

        order_msg = OrderMessage(
            orderid=order_id,
            userid=user_id,
            messageid=message_id,
            chatid=user_id
        )
        session.add(order_msg)
        await session.commit()


async def get_order_message(order_id: int) -> Optional[Dict[str, Any]]:
    """Получение message_id заказа"""
    async with async_session() as session:
        result = await session.execute(
            select(OrderMessage).where(OrderMessage.orderid == order_id)
        )
        msg = result.scalar_one_or_none()

        if not msg:
            return None

        return {
            "chat_id": msg.chatid,
            "message_id": msg.messageid,
            "order_id": msg.orderid,
        }


# ===== ФУНКЦИИ ДЛЯ АДМИНКИ =====

async def get_orders_by_status(status: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Получить заказы по статусу для админки"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.status == status)
            .order_by(Order.createdat.desc())
            .limit(limit)
        )
        orders = result.scalars().all()
        
        return [
            {
                "id": order.id,
                "user_id": order.userid,
                "total_price": float(order.total),
                "status": order.status,
                "delivery_type": order.deliverytype or "delivery",
                "address": order.address or "",
                "phone": order.phone or "",
                "name": order.name or "",
                "created_at": order.createdat.isoformat() if order.createdat else None,
            }
            for order in orders
        ]


async def update_order_status_by_id(order_id: int, new_status: str) -> bool:
    """Обновить статус заказа по ID"""
    async with async_session() as session:
        now = datetime.now()
        
        result = await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=new_status, updatedat=now)
        )
        
        history = OrderHistory(
            orderid=order_id,
            status=new_status,
            paymentstatus="not_paid",
            changedat=now,
            comment=f"Статус изменён на {new_status}"
        )
        session.add(history)
        
        await session.commit()
        return result.rowcount > 0
# ===== МАРКЕТИНГ =====

async def update_marketing_consent(user_id: int, consent: bool):
    """Обновление согласия на рассылку"""
    async with async_session() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.userid == user_id)
            .values(consentmarketing=consent)
        )
        await session.commit()


async def get_users_with_consent() -> List[Dict[str, Any]]:
    """Получение пользователей с согласием на рассылку"""
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.consentmarketing == True)
        )
        users = result.scalars().all()

        return [
            {
                "user_id": user.userid,
                "name": user.fullname,
                "phone": user.phone,
            }
            for user in users
        ]


# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====

async def get_last_orders(limit: int = 10) -> List[Dict[str, Any]]:
    """Получить последние заказы"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .order_by(Order.createdat.desc())
            .limit(limit)
        )
        orders = result.scalars().all()

        return [
            {
                "id": order.id,
                "user_id": order.userid,
                "name": order.name,
                "phone": order.phone,
                "address": order.address,
                "delivery_type": order.deliverytype,
                "status": order.status,
                "payment_status": order.paymentstatus,
                "total": order.total,
                "created_at": int(order.createdat.timestamp()) if order.createdat else 0,
            }
            for order in orders
        ]


async def save_order(user_id: int, order_data: Dict[str, Any]) -> str:
    """Сохранить заказ (генерирует номер заказа)"""
    async with async_session() as session:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        order_number = f"SP-{timestamp}-{user_id}"

        order = Order(
            userid=user_id,
            name=order_data['customer_name'],
            phone=order_data['customer_phone'],
            deliverytype=order_data['delivery_method'],
            address=order_data.get('delivery_address'),
            paymenttype=order_data['payment_method'],
            total=order_data['total_amount'],
            status='new',
            paymentstatus='not_paid',
            createdat=datetime.now(),
            updatedat=datetime.now()
        )

        session.add(order)
        await session.flush()

        # Добавляем позиции
        for item in order_data['items']:
            order_item = OrderItem(
                orderid=order.id,
                productcode=item.get('product_code'),
                name=item['name'],
                quantity=item['quantity'],
                price=item['price']
            )
            session.add(order_item)

        await session.commit()
        return order_number


async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    """Получить заказ по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        return {
            "id": order.id,
            "user_id": order.userid,
            "name": order.name,
            "phone": order.phone,
            "address": order.address,
            "delivery_type": order.deliverytype,
            "status": order.status,
            "payment_status": order.paymentstatus,
            "total": order.total,
            "created_at": int(order.createdat.timestamp()) if order.createdat else 0,
            "updated_at": int(order.updatedat.timestamp()) if order.updatedat else 0,
        }


async def get_order_items(order_id: int) -> List[Dict[str, Any]]:
    """Получить позиции заказа"""
    async with async_session() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.orderid == order_id)
        )
        items = result.scalars().all()

        return [
            {
                "product_code": item.productcode,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "weight": item.weight,
            }
            for item in items
        ]


async def update_order_status_db(
    order_id: int,
    new_status: str,
    payment_status: Optional[str],
    admin_id: Optional[int],
    comment: str,
):
    """Обновить статус заказа (расширенная версия)"""
    async with async_session() as session:
        now = datetime.now()

        # Обновляем заказ
        if payment_status:
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(status=new_status, paymentstatus=payment_status, updatedat=now)
            )
        else:
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(status=new_status, updatedat=now)
            )

            # Получаем текущий payment_status
            result = await session.execute(
                select(Order.paymentstatus).where(Order.id == order_id)
            )
            payment_status = result.scalar_one_or_none() or "not_paid"

        # Записываем в историю
        history = OrderHistory(
            orderid=order_id,
            status=new_status,
            paymentstatus=payment_status,
            changedat=now,
            changedby=admin_id,
            comment=comment
        )
        session.add(history)

        await session.commit()


async def get_all_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Получить все заказы (для админа)"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .order_by(Order.createdat.desc())
            .limit(limit)
        )
        orders = result.scalars().all()

        output = []
        for order in orders:
            # Получаем items
            items_result = await session.execute(
                select(OrderItem).where(OrderItem.orderid == order.id)
            )
            items = items_result.scalars().all()

            output.append({
                'id': order.id,
                'order_number': f"#{order.id}",
                'user_id': order.userid,
                'customer_name': order.name,
                'customer_phone': order.phone,
                'total_amount': order.total,
                'status': order.status,
                'created_at': order.createdat.isoformat() if order.createdat else "",
                'items': [
                    {
                        "name": item.name,
                        "quantity": item.quantity,
                        "price": item.price,
                    }
                    for item in items
                ],
                'delivery_method': order.deliverytype,
                'payment_method': order.paymenttype,
                'delivery_address': order.address,
            })

        return output


async def update_order_status(order_number: str, new_status: str) -> bool:
    """Обновить статус заказа по номеру"""
    # Извлекаем ID из номера заказа
    try:
        order_id = int(order_number.replace("#", "").replace("SP-", "").split("-")[-1])
    except:
        return False
    
    return await update_order_status_by_id(order_id, new_status)

async def update_user_profile(user_id: int, profile_data: Dict[str, Any]):
    """Обновить профиль"""
    await upsert_user_profile(user_id, profile_data)