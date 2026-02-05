@echo off
echo ===================================================
echo 🚀 Запуск ChefPort (Локально)
echo ===================================================

if exist venv311 (
    echo [INFO] Найдено окружение venv311. Активация...
    call venv311\Scripts\activate
) else (
    echo [INFO] Окружение venv311 не найдено. Пробуем venv...
    call venv\Scripts\activate
)

echo.
echo 2. Установка зависимостей?
set /p install_deps="Установить/Обновить библиотеки? (y/n, по умолчанию n): "
if /i "%install_deps%"=="y" (
    echo Установка...
    pip install -r requirements.txt
    pip install -r bot/requirements.txt
    pip install uvicorn fastapi python-dotenv sqlalchemy asyncpg aiogram
) else (
    echo Пропуск установки.
)

echo.
echo 3. Запуск API и Бота...
echo.
echo [INFO] Сейчас откроются два окна. Если в них красные ошибки - значит библиотеки НЕ установились.
echo.

start "ChefPort API" cmd /k "python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
start "ChefPort BOT" cmd /k "python -m bot.bot_complete"

echo ✅ Готово! API и Бот запущены в новых окнах.
echo 🌐 API доступно по адресу: http://localhost:8000
echo 🤖 Бот работает в Telegram.
pause
