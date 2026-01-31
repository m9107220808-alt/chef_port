from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse  # <-- Добавили этот импорт
from api.config import settings
from api.routes import products, orders, users

# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.0.0"
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
app.include_router(products.router, prefix="/api/products", tags=["Товары"])
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])

# ЗАМЕНИЛИ старый @app.get("/") на этот:
@app.get("/", response_class=HTMLResponse)
async def root_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Шеф Порт</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>/* твой CSS */</style>
    </head>
    <body>
        <div class="card">
            <div class="icon">🌊</div>
            <h1>Шеф Порт</h1>
            <p>Mini App готово!</p>
            <div id="status">Инициализация...</div>
        </div>
        <script>
            // ОБЯЗАТЕЛЬНО ДЛЯ TELEGRAM
            window.Telegram?.WebApp.ready();
            window.Telegram?.WebApp.expand();
            
            const user = window.Telegram?.WebApp.initDataUnsafe?.user;
            document.getElementById('status').innerHTML = 
                `✅ Готово! ID: ${user?.id || 'нет данных'}`;
                
            console.log('User:', user);
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Блок запуска (оставляем без изменений)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
