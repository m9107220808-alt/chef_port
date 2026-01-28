import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS

# ✅ ИМПОРТИРУЕМ АСИНХРОННЫЕ ФУНКЦИИ
from bot.db_postgres import (
    get_orders_by_status,
    get_order_details,
    update_order_status_by_id,
    get_order_message,
    get_user_profile,
)

logger = logging.getLogger(__name__)
router = Router()

# Статусы заказов
STATUS_TITLES = {
    "new": "🆕 Новые заказы",
    "cooking": "👨‍🍳 В обработке / сборке",
    "delivering": "🚚 В доставке",
    "ready": "🏃 Готов к самовывозу",
    "completed": "✅ Выполненные",
    "cancelled": "❌ Отменённые",
}

STATUS_EMOJI = {
    "new": "🆕",
    "confirmed": "✅",
    "cooking": "👨‍🍳",
    "delivering": "🚚",
    "completed": "🎉",
    "cancelled": "❌",
    "ready": "🏃",
}


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Главное меню админки"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 Новые", callback_data="admin:orders:new")
    kb.button(text="👨‍🍳 В обработке", callback_data="admin:orders:cooking")
    kb.button(text="🚚 В доставке", callback_data="admin:orders:delivering")
    kb.button(text="🏃 Самовывоз", callback_data="admin:orders:ready")
    kb.button(text="✅ Выполнены", callback_data="admin:orders:completed")
    kb.button(text="❌ Отменены", callback_data="admin:orders:cancelled")
    kb.adjust(2, 2, 2)

    text = (
        "🔧 <b>Админ‑панель Chef Port</b>\n\n"
        "Выберите, какие заказы показать:"
    )

    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("admin:orders:"))
async def admin_show_orders_by_status(callback: CallbackQuery):
    """Список заказов по статусу"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    status = callback.data.split(":")[-1]
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    orders = await get_orders_by_status(status, limit=20)

    if not orders:
        await callback.answer("📭 Нет заказов с таким статусом", show_alert=True)
        return

    title = STATUS_TITLES.get(status, "Заказы")
    text = f"{title}\n\n"

    kb = InlineKeyboardBuilder()
    for order in orders:
        name = order.get("name", "Неизвестно")
        
        text += (
            f"#{order['id']} — {name}\n"
            f"💰 {order['total_price']} ₽ | 📞 {order['phone']}\n\n"
        )
        
        kb.button(
            text=f"📋 #{order['id']}",
            callback_data=f"admin:order:{order['id']}",
        )

    kb.button(text="⬅️ Назад", callback_data="admin:back")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:") & ~F.data.contains(":confirm:") & ~F.data.contains(":cancel:") & ~F.data.contains(":deliver:") & ~F.data.contains(":complete:"))
async def admin_view_order(callback: CallbackQuery):
    """Просмотр деталей заказа"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    order = await get_order_details(order_id)

    if not order:
        await callback.answer(f"❌ Заказ #{order_id} не найден", show_alert=True)
        return

    # Формируем текст
    emoji = STATUS_EMOJI.get(order["status"], "📦")
    text = f"{emoji} <b>Заказ #{order['order_id']}</b>\n\n"
    text += f"👤 {order['name']}\n"
    text += f"📞 {order['phone']}\n"
    text += f"📍 {order['address']}\n\n"
    text += "🛒 <b>Товары:</b>\n"
    
    for item in order['items']:
        line_sum = item['price'] * item['quantity']
        text += f"• {item['name']} × {item['quantity']} = {line_sum} ₽\n"
    
    text += f"\n💰 <b>Итого: {order['total']} ₽</b>\n"
    text += f"📊 Статус: {order['status']}\n"
    text += f"💳 Оплата: {order['payment_type']}"

    # Кнопки действий
    kb = InlineKeyboardBuilder()
    
    if order["status"] == "new":
        kb.button(text="✅ Подтвердить", callback_data=f"admin:confirm:{order_id}")
        kb.button(text="❌ Отменить", callback_data=f"admin:cancel:{order_id}")
    elif order["status"] == "cooking":
        kb.button(text="🚚 В доставку", callback_data=f"admin:deliver:{order_id}")
        kb.button(text="✅ Завершить", callback_data=f"admin:complete:{order_id}")
    elif order["status"] == "delivering":
        kb.button(text="✅ Доставлен", callback_data=f"admin:complete:{order_id}")
    
    kb.button(text="⬅️ Назад к списку", callback_data=f"admin:orders:{order['status']}")
    kb.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm:"))
async def admin_confirm_order(callback: CallbackQuery, bot: Bot):
    """Подтвердить заказ"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    
    # Обновляем статус
    success = await update_order_status_by_id(order_id, "cooking")
    
    if not success:
        await callback.answer("❌ Ошибка обновления", show_alert=True)
        return

    # Уведомляем клиента
    order = await get_order_details(order_id)
    order_msg = await get_order_message(order_id)
    
    if order_msg:
        try:
            await bot.send_message(
                chat_id=order_msg["chat_id"],
                text=f"✅ Ваш заказ #{order_id} подтверждён и готовится!"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить клиента: {e}")

    await callback.answer("✅ Заказ подтверждён!", show_alert=True)
    
    # Перерисовываем карточку заказа
    callback.data = f"admin:order:{order_id}"
    await admin_view_order(callback)


@router.callback_query(F.data.startswith("admin:deliver:"))
async def admin_deliver_order(callback: CallbackQuery, bot: Bot):
    """Передать в доставку"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    
    success = await update_order_status_by_id(order_id, "delivering")
    
    if not success:
        await callback.answer("❌ Ошибка обновления", show_alert=True)
        return

    order_msg = await get_order_message(order_id)
    if order_msg:
        try:
            await bot.send_message(
                chat_id=order_msg["chat_id"],
                text=f"🚚 Ваш заказ #{order_id} передан в доставку!"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить клиента: {e}")

    await callback.answer("✅ Передано в доставку!", show_alert=True)
    
    callback.data = f"admin:order:{order_id}"
    await admin_view_order(callback)


@router.callback_query(F.data.startswith("admin:complete:"))
async def admin_complete_order(callback: CallbackQuery, bot: Bot):
    """Завершить заказ"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    
    success = await update_order_status_by_id(order_id, "completed")
    
    if not success:
        await callback.answer("❌ Ошибка обновления", show_alert=True)
        return

    order_msg = await get_order_message(order_id)
    if order_msg:
        try:
            await bot.send_message(
                chat_id=order_msg["chat_id"],
                text=f"🎉 Ваш заказ #{order_id} выполнен!\n\nСпасибо за покупку! Ждём вас снова! 😊"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить клиента: {e}")

    await callback.answer("✅ Заказ завершён!", show_alert=True)
    
    callback.data = f"admin:order:{order_id}"
    await admin_view_order(callback)


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel_order(callback: CallbackQuery, bot: Bot):
    """Отменить заказ"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[-1])
    
    success = await update_order_status_by_id(order_id, "cancelled")
    
    if not success:
        await callback.answer("❌ Ошибка обновления", show_alert=True)
        return

    order_msg = await get_order_message(order_id)
    if order_msg:
        try:
            await bot.send_message(
                chat_id=order_msg["chat_id"],
                text=f"❌ Ваш заказ #{order_id} отменён.\n\nПо вопросам обращайтесь к администратору."
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить клиента: {e}")

    await callback.answer("❌ Заказ отменён", show_alert=True)
    
    callback.data = f"admin:order:{order_id}"
    await admin_view_order(callback)


@router.callback_query(F.data == "admin:back")
async def admin_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню админки"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 Новые", callback_data="admin:orders:new")
    kb.button(text="👨‍🍳 В обработке", callback_data="admin:orders:cooking")
    kb.button(text="🚚 В доставке", callback_data="admin:orders:delivering")
    kb.button(text="🏃 Самовывоз", callback_data="admin:orders:ready")
    kb.button(text="✅ Выполнены", callback_data="admin:orders:completed")
    kb.button(text="❌ Отменены", callback_data="admin:orders:cancelled")
    kb.adjust(2, 2, 2)

    text = (
        "🔧 <b>Админ‑панель Chef Port</b>\n\n"
        "Выберите, какие заказы показать:"
    )
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()
