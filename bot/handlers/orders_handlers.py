import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ✅ ИМПОРТИРУЕМ АСИНХРОННЫЕ ФУНКЦИИ
from bot.db_postgres import (
    get_order_details,
    get_orders_with_items,
    get_cart_db,
    add_to_cart_db,
    get_product_by_id,
)

logger = logging.getLogger(__name__)
router = Router()


# ===== ГЛАВНОЕ МЕНЮ ЗАКАЗОВ =====

@router.message(F.text == "📋 Мои заказы")
async def my_orders_menu(message: Message):
    """Меню выбора количества заказов для отображения"""
    user_id = message.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    orders = await get_orders_with_items(user_id, limit=None)
    total_orders = len(orders)
    
    if total_orders == 0:
        await message.answer(
            "📋 У вас пока нет заказов\n\n"
            "Перейдите в каталог, чтобы сделать первый заказ! 🛍️"
        )
        return
    
    # Меню выбора
    text = f"📋 Мои заказы\n\n"
    text += f"Всего заказов: {total_orders}\n\n"
    text += "Выберите, сколько заказов отобразить:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Последние 5", callback_data="orders:show:5")
    kb.button(text="📅 Последние 10", callback_data="orders:show:10")
    kb.button(text="📅 Все заказы", callback_data="orders:show:all")
    kb.button(text="🛍️ В каталог", callback_data="catalog")
    kb.adjust(2, 1, 1)
    
    await message.answer(text, reply_markup=kb.as_markup())


# ===== ОТОБРАЖЕНИЕ СПИСКА ЗАКАЗОВ =====

@router.callback_query(F.data.startswith("orders:show:"))
async def show_orders_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    limit_str = callback.data.split(":")[-1]
    limit = None if limit_str == "all" else int(limit_str)
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    orders = await get_orders_with_items(user_id, limit)
    
    if not orders:
        await callback.answer("Заказов не найдено", show_alert=True)
        return

    text = f"📋 <b>Ваши заказы</b>\n"
    text += "━━━━━━━━━━━━━━━━\n"
    
    status_emoji = {
        "new": "🆕",
        "confirmed": "✅",
        "cooking": "👨‍🍳",
        "delivering": "🚚",
        "ready": "🏃",
        "completed": "🎉",
        "cancelled": "❌"
    }
    
    kb = InlineKeyboardBuilder()

    for order in orders:
        emoji = status_emoji.get(order['status'], "🔄")
        dt = datetime.fromtimestamp(order['created_at']).strftime("%d.%m.%Y %H:%M")
        
        text += f"\n📦 <b>Заказ #{order['id']}</b> ({dt})\n"
        for item in order['items']:
            qty = item['qty']
            price = item['price']
            line_total = int(qty * price)
            text += f" • {item['name']} × {qty} = {line_total} ₽\n"
        
        text += f"💰 <b>Итого: {int(order['total'])} ₽</b> | {emoji}\n"
        text += "━━━━━━━━━━━━━━━━\n"
        
        # Кнопки для каждого заказа
        kb.button(text=f"📋 #{order['id']}", callback_data=f"order:view:{order['id']}")
        kb.button(text=f"🔁 Повтор", callback_data=f"order:repeat:{order['id']}")
    
    kb.button(text="◀️ Назад", callback_data="orders:back_menu")
    kb.adjust(2)  # По 2 кнопки в ряд
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


# ===== ВОЗВРАТ В МЕНЮ ЗАКАЗОВ =====

@router.callback_query(F.data == "orders:back_menu")
async def back_to_orders_menu(callback: CallbackQuery):
    """Возврат к меню выбора количества заказов"""
    user_id = callback.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    orders = await get_orders_with_items(user_id, limit=None)
    total_orders = len(orders)
    
    text = f"📋 Мои заказы\n\n"
    text += f"Всего заказов: {total_orders}\n\n"
    text += "Выберите, сколько заказов отобразить:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Последние 5", callback_data="orders:show:5")
    kb.button(text="📅 Последние 10", callback_data="orders:show:10")
    kb.button(text="📅 Все заказы", callback_data="orders:show:all")
    kb.button(text="🛍️ В каталог", callback_data="catalog")
    kb.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


# ===== ПРОСМОТР ЗАКАЗА =====

@router.callback_query(F.data.startswith("order:view:"))
async def view_order(callback: CallbackQuery):
    """Просмотр деталей заказа"""
    order_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    order = await get_order_details(order_id)
    
    if not order or order['user_id'] != user_id:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    status_emoji = {
        "new": "🆕 Новый",
        "confirmed": "✅ Подтверждён",
        "cooking": "👨‍🍳 Готовится",
        "preparing": "📦 Упаковывается",
        "ready": "✅ Готов к выдаче",
        "delivering": "🚚 В доставке",
        "completed": "🎉 Завершён",
        "cancelled": "❌ Отменён"
    }
    
    payment_types = {
        "cash_no_change": "💵 Наличные без сдачи",
        "cash_change": "💵 Наличные со сдачей",
        "card": "💳 Безнал (перевод)"
    }
    
    # Форматируем дату
    try:
        dt = datetime.fromtimestamp(order['created_at'])
        date_str = dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        date_str = "—"
    
    text = f"📋 Заказ #{order['order_id']}\n"
    text += f"📅 {date_str}\n\n"
    text += "🛒 Состав:\n"
    
    for item in order['items']:
        line_sum = item['price'] * item['quantity']
        text += f"• {item['name']} × {item['quantity']} = {int(line_sum)} ₽\n"
    
    text += f"\n💰 Итого: {int(order['total'])} ₽\n"
    text += f"💳 Оплата: {payment_types.get(order['payment_type'], 'Наличные')}\n"
    text += f"📊 Статус: {status_emoji.get(order['status'], '🔄')}\n\n"
    text += f"📍 Адрес: {order['address']}\n"
    text += f"📞 Телефон: {order['phone']}"
    
    kb = InlineKeyboardBuilder()
    
    # Кнопка "Повторить заказ" для завершённых или отменённых
    if order['status'] in ['completed', 'cancelled']:
        kb.button(text="🔁 Повторить заказ", callback_data=f"order:repeat:{order_id}")
    
    # Кнопка "Отменить" для новых и подтверждённых
    if order['status'] in ['new', 'confirmed']:
        kb.button(text="❌ Отменить заказ", callback_data=f"order:cancel:{order_id}")
    
    kb.button(text="◀️ К списку заказов", callback_data="orders:show:10")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


# ===== ПОВТОР ЗАКАЗА =====

@router.callback_query(F.data.startswith("order:repeat:"))
async def repeat_order(callback: CallbackQuery):
    """Повтор заказа"""
    order_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    order = await get_order_details(order_id)
    
    if not order or order['user_id'] != user_id:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Копируем товары в корзину
    try:
        for item in order['items']:
            # Ищем товар по product_code
            product_code = item.get('product_code')
            if product_code:
                await add_to_cart_db(user_id, product_code, item['quantity'])
        
        logger.info(f"Заказ #{order_id} скопирован в корзину для user {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при повторе заказа: {e}")
        await callback.answer("❌ Ошибка при копировании заказа", show_alert=True)
        return
    
    # Показываем корзину
    cart_items = await get_cart_db(user_id)
    
    if not cart_items:
        await callback.answer("❌ Не удалось скопировать товары", show_alert=True)
        return
    
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    
    text = f"✅ Заказ #{order_id} скопирован в корзину!\n\n"
    text += "🛒 Ваша корзина:\n"
    
    for item in cart_items:
        line_sum = item["price"] * item["quantity"]
        text += f"• {item['name']} × {item['quantity']} = {int(line_sum)} ₽\n"
    
    text += f"\n💰 Итого: {int(total)} ₽"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Оформить заказ", callback_data="checkout")
    kb.button(text="🛍️ Продолжить покупки", callback_data="catalog")
    kb.button(text="🗑️ Очистить корзину", callback_data="clear_cart")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer("🔁 Заказ скопирован!")


# ===== ОТМЕНА ЗАКАЗА =====

@router.callback_query(F.data.startswith("order:cancel:"))
async def cancel_order(callback: CallbackQuery):
    """Отмена заказа клиентом"""
    order_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    order = await get_order_details(order_id)
    
    if not order or order['user_id'] != user_id:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Проверяем статус
    if order['status'] not in ['new', 'confirmed']:
        await callback.answer("Этот заказ уже нельзя отменить", show_alert=True)
        return
    
    # Подтверждение отмены
    text = f"❓ Отменить заказ #{order_id}?\n\n"
    text += "Вы действительно хотите отменить этот заказ?"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, отменить", callback_data=f"order:cancel_confirm:{order_id}")
    kb.button(text="❌ Нет, вернуться", callback_data=f"order:view:{order_id}")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("order:cancel_confirm:"))
async def cancel_order_confirm(callback: CallbackQuery):
    """Подтверждение отмены заказа"""
    order_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # ✅ АСИНХРОННЫЙ ЗАПРОС
    order = await get_order_details(order_id)
    
    if not order or order['user_id'] != user_id:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # ✅ ИСПОЛЬЗУЕМ ASYNC ФУНКЦИЮ (добавим её в db_postgres.py)
    from bot.db_postgres import update_order_status_by_id
    
    success = await update_order_status_by_id(order_id, "cancelled")
    
    if not success:
        await callback.answer("❌ Ошибка отмены заказа", show_alert=True)
        return
    
    text = f"✅ Заказ #{order_id} отменён\n\n"
    text += "Если у вас возникли вопросы, свяжитесь с нами."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ К списку заказов", callback_data="orders:show:10")
    kb.button(text="🛍️ В каталог", callback_data="catalog")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer("Заказ отменён")
    
    logger.info(f"Заказ #{order_id} отменён пользователем {user_id}")


# ===== ВОЗВРАТ К СПИСКУ ЗАКАЗОВ (для других хендлеров) =====

@router.callback_query(F.data == "orders:list")
async def orders_list_inline(callback: CallbackQuery):
    """Быстрый возврат к последним 10 заказам"""
    callback.data = "orders:show:10"
    await show_orders_list(callback)
