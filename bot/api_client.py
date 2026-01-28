import aiohttp
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Product:
    """Класс товара для бота"""
    id: int
    name: str
    description: Optional[str]
    price: float
    weight: Optional[float]
    unit: str
    image_url: Optional[str]
    category: Optional[str]
    in_stock: bool

@dataclass
class OrderItem:
    """Класс позиции заказа"""
    product_id: int
    quantity: int

class APIClient:
    """Клиент для работы с ChefPort API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_products(
        self, 
        category: Optional[str] = None,
        in_stock: Optional[bool] = True
    ) -> List[Product]:
        """Получить список товаров"""
        params = {}
        if category:
            params['category'] = category
        if in_stock is not None:
            params['in_stock'] = str(in_stock).lower()
        
        async with self.session.get(f"{self.base_url}/api/products/", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return [Product(**item) for item in data]
            return []
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Получить один товар"""
        async with self.session.get(f"{self.base_url}/api/products/{product_id}") as resp:
            if resp.status == 200:
                data = await resp.json()
                return Product(**data)
            return None
    
    async def create_user(self, telegram_id: int, username: Optional[str] = None, 
                         first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
        """Создать или обновить пользователя"""
        user_data = {
            "id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        }
        
        async with self.session.post(f"{self.base_url}/api/users/", json=user_data) as resp:
            return await resp.json()
    
    async def create_order(
        self, 
        user_id: int, 
        delivery_address: str,
        items: List[OrderItem],
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создать заказ"""
        order_data = {
            "user_id": user_id,
            "delivery_address": delivery_address,
            "comment": comment,
            "items": [{"product_id": item.product_id, "quantity": item.quantity} for item in items]
        }
        
        async with self.session.post(f"{self.base_url}/api/orders/", json=order_data) as resp:
            if resp.status == 201:
                return await resp.json()
            else:
                error = await resp.text()
                raise Exception(f"Ошибка создания заказа: {error}")
    
    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить заказы пользователя"""
        async with self.session.get(f"{self.base_url}/api/orders/", params={"user_id": user_id}) as resp:
            if resp.status == 200:
                return await resp.json()
            return []
