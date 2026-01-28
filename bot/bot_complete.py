import asyncio
import logging
import os
from functools import partial
from dotenv import load_dotenv

# ✅ Импорты aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from aiogram.fsm.storage.memory import MemoryStorage

# ✅ Импорты обработчиков
from bot.handlers.user_handlers import router as user_router
from bot.handlers.admin_handlers import router as admin_router
from bot.handlers.orders_handlers import router as orders_router
from bot.handlers.profile_handlers import router as profile_router

# ✅ Импорт checkout из корня bot/ (НЕ из handlers/)
from bot.handlers.checkout_handlers import router as checkout_router

from bot.config import BOT_TOKEN, ADMIN_IDS

# Инициализация БД и демо-данных
from bot.db_postgres import create_tables, init_demo_catalog

ADMIN_IDS = [878283648]

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env")


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("🚀 Chef Port Bot запущен")
    
    # ✅ ШАГ 1: Удаляем ВСЕ старые команды для всех scope
    await bot.delete_my_commands()
    await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    
    # Для каждого админа тоже очищаем
    for admin_id in ADMIN_IDS:
        try:
            await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception:
            pass
    
    # Создаём таблицы БД
    await create_tables()
    await init_demo_catalog()
    
    # ✅ ШАГ 2: Команды для обычных пользователей
    user_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="❓ Справка"),
    ]
    
    await bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeAllPrivateChats()
    )
    
    # ✅ ШАГ 3: Команды для администраторов
    admin_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="admin", description="🔧 Админ-панель"),
        BotCommand(command="help", description="❓ Справка"),
    ]
    
    for admin_id in ADMIN_IDS:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=admin_id)
        )
    
    logger.info("✅ Команды установлены")


async def main():
    """Главная функция запуска бота"""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(orders_router)
    dp.include_router(profile_router)
    dp.include_router(checkout_router)  # ← Новый checkout роутер
    
    # Регистрируем on_startup
    dp.startup.register(partial(on_startup, bot))
    
    logger.info("✅ Все обработчики зарегистрированы")
    logger.info("🟢 Chef Port Bot готов к работе")
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
