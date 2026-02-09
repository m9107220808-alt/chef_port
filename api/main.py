from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os

from api.config import settings
from api.routes import products, orders, users, settings as settings_router, uploads
from api.routes import upload
from api.database import get_db
from api.models.product import Product
from api.schemas.product import ProductResponse
from api.models.category import Category
from api.schemas.category import CategoryResponse

# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.5.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Настройки"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Загрузка"])
app.include_router(upload.router, prefix="/api", tags=["Загрузка 2"])
app.include_router(products.router, prefix="/api/products", tags=["Товары"])
# app.include_router(categories.router, prefix="/api/categories", tags=["Категории"]) # If categories router exists

# API: Категории (Inline v1.4 - Keeping this if categories.py router is not fully ready/imported)
# Actually, let's check if categories router exists. If not, keep inline.
# Ideally we should move this to category router too, but let's fix products first.
@app.get("/api/categories", response_model=List[CategoryResponse], tags=["Категории"])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Получить все категории"""
    result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    return categories

# NOTE: Removed inline /api/products because we included products.router above

# Путь к папке web
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Подключение статики для изображений
IMAGES_DIR = os.path.join(WEB_DIR, "images")
if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Подключаем всю папку web для путей вида /web/images/...
if os.path.exists(WEB_DIR):
    app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")

@app.get("/products_data.js")
async def get_products_data_js():
    file_path = os.path.join(WEB_DIR, "products_data.js")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/javascript")
    return HTMLResponse(content="console.warn('products_data.js not found');", status_code=404)

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
