from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routes import products, orders, users


# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.0.0"
)

# Настройка CORS (для Mini Apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замени на конкретные домены!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(products.router, prefix="/api/products", tags=["Товары"])
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "ChefPort API работает!",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True  # Авто-перезагрузка при изменениях
    )
