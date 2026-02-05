from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os

from api.config import settings
from api.routes import products, orders, users
from api.database import get_db
from api.models.product import Product
from api.models.category import Category
from api.schemas.product import ProductResponse
from api.schemas.category import CategoryResponse

# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.0.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты (products закомментирован - используем свой эндпоинт выше)
# app.include_router(products.router, prefix="/api/products", tags=["Товары"])
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])

# API: Категории
@app.get("/api/categories", response_model=List[CategoryResponse], tags=["Категории"])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Получить все категории"""
    result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    return categories

# API: Все продукты (для Mini App)
@app.get("/api/products", response_model=List[ProductResponse], tags=["Товары"])
async def get_all_products(db: AsyncSession = Depends(get_db)):
    """Получить все продукты"""
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products

# Путь к папке web
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Подключение статики для изображений
IMAGES_DIR = os.path.join(WEB_DIR, "images")
if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

@app.get("/app/client", response_class=HTMLResponse)
async def get_client_app():
    return FileResponse(os.path.join(WEB_DIR, "miniapp_client.html"))

@app.get("/app/admin", response_class=HTMLResponse)
async def get_admin_app():
    return FileResponse(os.path.join(WEB_DIR, "miniapp_admin.html"))

@app.get("/app/delivery", response_class=HTMLResponse)
async def get_delivery_app():
    return FileResponse(os.path.join(WEB_DIR, "miniapp_delivery.html"))

@app.get("/", response_class=HTMLResponse)
async def root_page():
    return FileResponse(os.path.join(WEB_DIR, "miniapp_client.html"))



@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
