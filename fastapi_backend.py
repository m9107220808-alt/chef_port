#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🐟 Chef Port FastAPI Backend
REST API для всех Mini Apps (клиент, админ, доставщик)
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

# Инициализация FastAPI
app = FastAPI(
    title="Chef Port API",
    description="🐟 API для доставки морепродуктов",
    version="3.0"
)

# CORS конфигурация
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== БАЗА ДАННЫХ =====

DB_PATH = os.getenv("DB_PATH", "shop.db")

def get_db():
    """Получение соединения с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===== МОДЕЛИ PYDANTIC =====

class Category(BaseModel):
    id: int
    code: str
    name: str
    sort_order: int

class Product(BaseModel):
    id: int
    category_id: int
    code: str
    name: str
    price_per_kg: float
    is_weighted: int
    min_weight_kg: float
    description: Optional[str] = None

class OrderItem(BaseModel):
    name: str
    qty: float
    price: float
    product_code: Optional[str] = None

class Order(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    address: str
    delivery_type: str
    total: float
    status: str
    payment_type: Optional[str] = None
    created_at: Optional[str] = None
    items: List[OrderItem] = []

class OrderStatusUpdate(BaseModel):
    status: str

# ===== МАРШРУТЫ: КАТЕГОРИИ И ТОВАРЫ =====

@app.get("/api/categories", response_model=List[Category])
async def  get_categories():
    """Получение всех категорий товаров"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, code, name, sort_order FROM categories ORDER BY sort_order")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Category(
            id=row['id'],
            code=row['code'],
            name=row['name'],
            sort_order=row['sort_order']
        )
        for row in rows
    ]

@app.get("/api/products", response_model=List[Product])
async def get_products(category: Optional[str] = Query(None)):
    """Получение товаров (опционально по категории)"""
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT p.id, p.category_id, p.code, p.name, p.price_per_kg,
                   p.is_weighted, p.min_weight_kg, p.description
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.code = ?
            ORDER BY p.name
        """, (category,))
    else:
        cursor.execute("""
            SELECT id, category_id, code, name, price_per_kg,
                   is_weighted, min_weight_kg, description
            FROM products
            ORDER BY name
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Product(
            id=row['id'],
            category_id=row['category_id'],
            code=row['code'],
            name=row['name'],
            price_per_kg=row['price_per_kg'],
            is_weighted=row['is_weighted'],
            min_weight_kg=row['min_weight_kg'],
            description=row['description']
        )
        for row in rows
    ]

# ===== МАРШРУТЫ: ЗАКАЗЫ КЛИЕНТА =====

@app.get("/api/client/orders/{user_id}", response_model=List[Order])
async def get_client_orders(user_id: int, limit: int = Query(10)):
    """Получение заказов клиента"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, name, phone, address, delivery_type, total, status, payment_type, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    
    orders_rows = cursor.fetchall()
    
    orders = []
    for order_row in orders_rows:
        order_id = order_row['id']
        
        # Получаем товары заказа
        cursor.execute("""
            SELECT name, quantity, price
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        items = [
            OrderItem(
                name=item['name'],
                qty=item['quantity'],
                price=item['price']
            )
            for item in cursor.fetchall()
        ]
        
        orders.append(Order(
            id=order_row['id'],
            user_id=order_row['user_id'],
            name=order_row['name'],
            phone=order_row['phone'],
            address=order_row['address'],
            delivery_type=order_row['delivery_type'],
            total=order_row['total'],
            status=order_row['status'],
            payment_type=order_row['payment_type'],
            created_at=order_row['created_at'],
            items=items
        ))
    
    conn.close()
    return orders

@app.post("/api/client/orders", response_model=Order)
async def create_order(order_data: Order):
    """Создание нового заказа"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Создаём заказ
    cursor.execute("""
        INSERT INTO orders (user_id, name, phone, address, delivery_type, total, status, payment_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_data.user_id,
        order_data.name,
        order_data.phone,
        order_data.address,
        order_data.delivery_type,
        order_data.total,
        "new",
        order_data.payment_type or "cash_no_change",
        now
    ))
    
    order_id = cursor.lastrowid
    
    # Добавляем товары
    for item in order_data.items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, item.name, item.qty, item.price))
    
    conn.commit()
    conn.close()
    
    return Order(
        id=order_id,
        user_id=order_data.user_id,
        name=order_data.name,
        phone=order_data.phone,
        address=order_data.address,
        delivery_type=order_data.delivery_type,
        total=order_data.total,
        status="new",
        payment_type=order_data.payment_type,
        created_at=now,
        items=order_data.items
    )

# ===== МАРШРУТЫ: АДМИН-ПАНЕЛЬ =====

@app.get("/api/admin/orders", response_model=List[Order])
async def admin_get_orders(status: Optional[str] = Query(None)):
    """Получение всех заказов для админа"""
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("""
            SELECT id, user_id, name, phone, address, delivery_type, total, status, payment_type, created_at
            FROM orders
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (status,))
    else:
        cursor.execute("""
            SELECT id, user_id, name, phone, address, delivery_type, total, status, payment_type, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT 100
        """)
    
    orders_rows = cursor.fetchall()
    
    orders = []
    for order_row in orders_rows:
        order_id = order_row['id']
        
        # Получаем товары заказа
        cursor.execute("""
            SELECT name, quantity, price
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        items = [
            OrderItem(
                name=item['name'],
                qty=item['quantity'],
                price=item['price']
            )
            for item in cursor.fetchall()
        ]
        
        orders.append(Order(
            id=order_row['id'],
            user_id=order_row['user_id'],
            name=order_row['name'],
            phone=order_row['phone'],
            address=order_row['address'],
            delivery_type=order_row['delivery_type'],
            total=order_row['total'],
            status=order_row['status'],
            payment_type=order_row['payment_type'],
            created_at=order_row['created_at'],
            items=items
        ))
    
    conn.close()
    return orders

@app.put("/api/admin/orders/{order_id}/status")
async def admin_update_order_status(order_id: int, update: OrderStatusUpdate):
    """Обновление статуса заказа"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "order_id": order_id, "new_status": update.status}

# ===== МАРШРУТЫ: ДОСТАВЩИКИ =====

@app.get("/api/delivery/orders", response_model=List[Order])
async def delivery_get_orders(status: Optional[str] = Query(None)):
    """Получение заказов для доставщика"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Доставщик видит только заказы на доставку, не завершённые
    query = """
        SELECT id, user_id, name, phone, address, delivery_type, total, status, payment_type, created_at
        FROM orders
        WHERE delivery_type = 'delivery' AND status IN ('ready', 'delivering', 'completed')
    """
    
    if status:
        query += " AND status = ?"
        cursor.execute(query + " ORDER BY created_at DESC", (status,))
    else:
        cursor.execute(query + " ORDER BY created_at ASC")
    
    orders_rows = cursor.fetchall()
    
    orders = []
    for order_row in orders_rows:
        order_id = order_row['id']
        
        # Получаем товары заказа
        cursor.execute("""
            SELECT name, quantity, price
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        items = [
            OrderItem(
                name=item['name'],
                qty=item['quantity'],
                price=item['price']
            )
            for item in cursor.fetchall()
        ]
        
        orders.append(Order(
            id=order_row['id'],
            user_id=order_row['user_id'],
            name=order_row['name'],
            phone=order_row['phone'],
            address=order_row['address'],
            delivery_type=order_row['delivery_type'],
            total=order_row['total'],
            status=order_row['status'],
            payment_type=order_row['payment_type'],
            created_at=order_row['created_at'],
            items=items
        ))
    
    conn.close()
    return orders

@app.put("/api/delivery/orders/{order_id}/status")
async def delivery_update_order_status(order_id: int, update: OrderStatusUpdate):
    """Доставщик обновляет статус доставки"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем, что статус валидный для доставки
    valid_statuses = ['ready', 'delivering', 'completed']
    if update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status for delivery")
    
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "order_id": order_id, "new_status": update.status}

# ===== СТАТИСТИКА =====

@app.get("/api/stats")
async def get_stats():
    """Общая статистика по заказам"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Общее количество заказов
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()['count']
    
    # Выручка
    cursor.execute("SELECT SUM(total) as total_revenue FROM orders WHERE status = 'completed'")
    revenue = cursor.fetchone()['total_revenue'] or 0
    
    # По статусам
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    """)
    
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_orders": total_orders,
        "total_revenue": revenue,
        "by_status": status_counts
    }

# ===== HEALTH CHECK =====

@app.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok", "service": "Chef Port API v3.0"}

# ===== ROOT =====

@app.get("/")
async def root():
    """Главная страница"""
    return {
        "name": "🐟 Chef Port API",
        "version": "3.0",
        "endpoints": {
            "categories": "/api/categories",
            "products": "/api/products",
            "client_orders": "/api/client/orders/{user_id}",
            "admin_orders": "/api/admin/orders",
            "delivery_orders": "/api/delivery/orders",
            "stats": "/api/stats",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True
    )