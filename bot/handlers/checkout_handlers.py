import logging
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from bot.states import CheckoutStates
from bot.db_postgres  import (
    get_cart_db,
    clear_cart_db,
    get_product_by_code,
    save_order,
    get_user_profile,
    upsert_user_profile,
    get_user_addresses,
    add_user_address
)

logger = logging.getLogger(__name__)
router = Router()

# ID администраторов (для уведомлений)
ADMIN_IDS = [878283648]  # ✅ ИСПРАВИЛ НА СПИСОК
PICKUP_ADDRESS = "г. Смоленск, ул. Багратиона, д. 2Б"

# ===== ЭМОДЗИ ДЛЯ ТОВАРОВ =====
PRODUCT_EMOJI = {
    "salmon": "🐟", "seabass": "🐠", "trout": "🐋", "tuna": "🦈",
    "dorado": "🐠", "herring": "🐟", "mackerel": "🐟", "cod": "🐟",
    "shrimp": "🦐", "prawn": "🦐", "crab": "🦀", "lobster": "🦞",
    "squid": "🦑", "octopus": "🐙", "oyster": "🦪", "mussel": "🦪",
    "scallop": "🦪", "red_caviar": "🔴", "black_caviar": "⚫",
    "caviar": "🔴⚫", "smoked_salmon": "🔥💥", "smoked": "🔥💥",
}

def get_product_emoji(prod_code: str) -> str:
    """Получить эмодзи для товара"""
    if prod_code in PRODUCT_EMOJI:
        return PRODUCT_EMOJI[prod_code]
    prod_lower = prod_code.lower()
    if "caviar" in prod_lower or "икра" in prod_lower:
        if "red" in prod_lower or "красн" in prod_lower:
            return "🔴"
        elif "black" in prod_lower or "черн" in prod_lower:
            return "⚫"
        return "🔴⚫"
    if "shrimp" in prod_lower or "креветк" in prod_lower or "prawn" in prod_lower:
        return "🦐"
    if "crab" in prod_lower or "краб" in prod_lower:
        return "🦀"
    if "lobster" in prod_lower or "лобстер" in prod_lower:
        return "🦞"
    if "squid" in prod_lower or "кальмар" in prod_lower:
        return "🦑"
    if "octopus" in prod_lower or "осьминог" in prod_lower:
        return "🐙"
    if "oyster" in prod_lower or "устриц" in prod_lower or "mussel" in prod_lower or "мидии" in prod_lower:
        return "🦪"
    return "🐟"

# ===== НАЧАЛО ОФОРМЛЕНИЯ ЗАКАЗА =====
@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    user_id = callback.from_user.id
    cart_items = await get_cart_db(user_id)
    
    if not cart_items:
        await callback.answer("🛒 Корзина пуста!", show_alert=True)
        return
    
    # Сохраняем корзину в state
    await state.update_data(cart_items=cart_items)
    
    # ✅ ПРОВЕРЯЕМ ПРОФИЛЬ
    profile = await get_user_profile(user_id)
    
    if profile:
        # ✅ ПРОФИЛЬ ЕСТЬ - ИСПОЛЬЗУЕМ ЕГО!
        await state.update_data(
            customer_name=profile['full_name'],
            customer_phone=profile['phone']
        )
        
        total = sum(item["price"] * item["quantity"] for item in cart_items)
        text = "🎊 Оформление заказа\n━━━━━━━━━━━━━━━━\n\n"
        text += f"💰 Сумма: {int(total)} ₽\n\n"
        text += f"👤 {profile['full_name']}\n"
        text += f"📞 {profile['phone']}\n\n"
        text += "🚚 Как получите заказ?"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🚚 Доставка", callback_data="delivery:delivery")
        kb.button(text="🏃 Самовывоз", callback_data="delivery:pickup")
        kb.button(text="✏️ Изменить данные", callback_data="checkout:edit_profile")
        kb.button(text="❌ Отменить", callback_data="cancel_checkout")
        kb.adjust(2, 1, 1)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await state.update_data(last_bot_message_id=callback.message.message_id)
        await state.set_state(CheckoutStates.choosing_delivery_method)
        await callback.answer()
        return
    
    # Показываем корзину и просим ввести имя
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    text = "🎊 Оформление заказа\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    text += "🛒 Ваш заказ:\n\n"
    
    for i, item in enumerate(cart_items, 1):
        emoji = get_product_emoji(item["product_code"])
        product = await get_product_by_code(item["product_code"])
        if product:
            is_weighted = product[4]
            item_total = item["price"] * item["quantity"]
            if is_weighted:
                text += f"{i}. {emoji} {item['name']}\n"
                text += f"   {item['quantity']} кг × {int(item['price'])} ₽ = {int(item_total)} ₽\n\n"
            else:
                text += f"{i}. {emoji} {item['name']}\n"
                text += f"   {int(item['quantity'])} шт × {int(item['price'])} ₽ = {int(item_total)} ₽\n\n"
    
    text += "━━━━━━━━━━━━━━━━\n"
    text += f"💰 Итого: {int(total)} ₽\n\n"
    text += "👤 Как вас зовут?\n"
    text += "Напишите ваше имя:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить оформление", callback_data="cancel_checkout")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_name)
    await callback.answer()


# ✅ ДОБАВЛЕН ОБРАБОТЧИК "ИЗМЕНИТЬ ДАННЫЕ"
@router.callback_query(F.data == "checkout:edit_profile")
async def checkout_edit_profile(callback: CallbackQuery, state: FSMContext):
    """Изменить данные при оформлении заказа"""
    text = "<b>👤 Введите новое имя:</b>\n\n"
    text += "Минимум 2 символа."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_name)
    await callback.answer()


# ===== ШАГ 1: ВВОД ИМЕНИ =====
@router.message(CheckoutStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработать имя клиента"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Пожалуйста, введите ваше настоящее имя:")
        return
    
    # Сохраняем имя
    await state.update_data(customer_name=name)
     # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    data = await state.get_data()
    
    # Просим телефон
    text = f"✅ Отлично, {name}!\n\n"
    text += "📞 Введите ваш номер телефона\n"
    text += "Формат: +7 (XXX) XXX-XX-XX или 89XXXXXXXXX"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить оформление", callback_data="cancel_checkout")
    
    if 'last_bot_message_id' in data:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data['last_bot_message_id'],
                text=text,
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )
            await state.update_data(last_bot_message_id=data['last_bot_message_id'])
        except Exception:
            msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=msg.message_id)
    else:
        msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await state.update_data(last_bot_message_id=msg.message_id)
    
    await state.set_state(CheckoutStates.waiting_for_phone)

# ===== ШАГ 2: ВВОД ТЕЛЕФОНА =====
@router.message(CheckoutStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработать номер телефона"""
    phone = message.text.strip()
    
     # ✅ Удаляем предыдущее сообщение бота
    data = await state.get_data()
    if "phone_request_message_id" in data:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data["phone_request_message_id"]
            )
        except TelegramBadRequest:
            pass
    await message.delete()     
    # Простая валидация телефона
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    if not re.match(r'^(\+7|8)\d{10}$', phone_clean):
        await message.answer(
            "❌ Неверный формат телефона!\n\n"
            "Пожалуйста, введите номер в формате:\n"
            "+7 (999) 123-45-67 или 89991234567"
        )
        return
    
    # Нормализуем телефон
    if phone_clean.startswith('8'):
        phone_clean = '+7' + phone_clean[1:]
     # ✅ Удалить старое сообщение с просьбой ввода
    if "prompt_message_id" in data:
        try:
            await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=data["prompt_message_id"]
                )
        except TelegramBadRequest:
            pass
    # Сохраняем телефон
    await state.update_data(customer_phone=phone_clean)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    # Выбор способа получения
    text = "✅ Телефон сохранён!\n\n"
    text += "🚚 Как вы хотите получить заказ?"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🚚 Доставка", callback_data="delivery:delivery")
    kb.button(text="🏃 Самовывоз", callback_data="delivery:pickup")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(2, 1)
    
    msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(CheckoutStates.choosing_delivery_method)


# ===== ШАГ 3: ВЫБОР СПОСОБА ДОСТАВКИ =====
@router.callback_query(F.data.startswith("delivery:"))
async def process_delivery_method(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор способа доставки"""
    method = callback.data.split(":")[1]
    await state.update_data(delivery_method=method)
    
    if method == "delivery":
        # ✅ ПОЛУЧАЕМ ВСЕ АДРЕСА ПОЛЬЗОВАТЕЛЯ
        user_id = callback.from_user.id
        addresses = await get_user_addresses(user_id)
        
        if addresses:
            # ✅ ПОКАЗЫВАЕМ СПИСОК АДРЕСОВ ДЛЯ ВЫБОРА!
            text = "📍 Выберите адрес доставки:\n\n"
            kb = InlineKeyboardBuilder()
            
            for addr in addresses:
                default_mark = "⭐ " if addr['is_default'] else ""
                text += f"• {default_mark}{addr['label']}\n"
                text += f"   {addr['address']}\n\n"
                kb.button(
                    text=f"{default_mark}{addr['label']}",
                    callback_data=f"select_delivery_address:{addr['id']}"
                )
            
            kb.button(text="➕ Ввести новый адрес", callback_data="enter_new_delivery_address")
            kb.button(text="❌ Отменить", callback_data="cancel_checkout")
            kb.adjust(1)
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=callback.message.message_id)
            await state.set_state(CheckoutStates.choosing_address)
            await callback.answer()
        else:
            # ✅ НЕТ АДРЕСОВ - ПРОСИМ ВВЕСТИ
            text = "📍 Введите адрес доставки:\n\n"
            text += "Пример: г. Смоленск, ул. Ленина, д. 10, кв. 5"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="❌ Отменить", callback_data="cancel_checkout")
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=callback.message.message_id)
            await state.set_state(CheckoutStates.waiting_for_address)
            await callback.answer()
    else:
        # ✅ САМОВЫВОЗ
        await state.update_data(delivery_address=PICKUP_ADDRESS)
        await ask_payment_method(callback.message, state, edit=True)
        await callback.answer()  # ✅ ДОБАВЛЕНО!


# ===== ШАГ 4: ВВОД АДРЕСА (если доставка) =====
@router.message(CheckoutStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработать введённый адрес"""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer(
            "❌ Адрес слишком короткий!\n\n"
            "Пожалуйста, укажите полный адрес:\n"
            "Например: г. Смоленск, ул. Ленина, д. 10, кв. 5"
        )
        return
    
    # ✅ Сохраняем адрес
    await state.update_data(delivery_address=address)
    
    # ✅ Удаляем сообщение пользователя
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    # ✅ Удаляем предыдущее сообщение бота
    data = await state.get_data()
    if 'last_bot_message_id' in data:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['last_bot_message_id']
            )
        except Exception:
            pass
    
    # ✅ ПРЕДЛАГАЕМ СОХРАНИТЬ АДРЕС!
    text = f"📍 Адрес: {address}\n\n"
    text += "💾 Сохранить этот адрес для будущих заказов?"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, сохранить", callback_data="save_new_addr:yes")
    kb.button(text="⏭️ Нет, продолжить", callback_data="save_new_addr:no")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(2, 1)
    
    msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(CheckoutStates.confirming_new_address)


@router.callback_query(F.data.startswith("save_new_addr:"))
async def save_new_address(callback: CallbackQuery, state: FSMContext):
    """Сохранить новый адрес или пропустить"""
    choice = callback.data.split(":")[1]
    data = await state.get_data()
    user_id = callback.from_user.id
    
    if choice == "yes":
        # Проверяем, первый ли это адрес
        addresses = await get_user_addresses(user_id)
        is_first = len(addresses) == 0
        
        # Сохраняем адрес
        await add_user_address(
            user_id,
            data['delivery_address'],
            label="Адрес",
            is_default=is_first
        )
    
    # Переходим к оплате
    await ask_payment_method(callback.message, state, edit=True)
    await callback.answer("✅ Сохранено!" if choice == "yes" else "")


@router.callback_query(F.data == "address:confirm")
async def confirm_address(callback: CallbackQuery, state: FSMContext):
    """Подтвердить адрес - переход к оплате"""
    await ask_payment_method(callback.message, state, edit=True)
    await callback.answer()


@router.callback_query(F.data == "address:edit")
async def edit_address(callback: CallbackQuery, state: FSMContext):
    """Изменить адрес - вернуться к вводу"""
    text = "🏠 Введите новый адрес доставки\n\nПример: ул. Ленина, д. 10, кв. 5, под. 2, этаж 3"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_address)
    await callback.answer()


# ✅ ИСПРАВЛЕНА ФУНКЦИЯ ask_payment_method
async def ask_payment_method(message, state: FSMContext, edit: bool = False):
    """Запрос оплаты"""
    text = "💳 Способ оплаты:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Наличные", callback_data="payment:cash")
    kb.button(text="💳 Картой", callback_data="payment:card")
    kb.button(text="🌐 Онлайн", callback_data="payment:online")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(2, 1, 1)
    
    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        except Exception:
            # ✅ ИСПРАВЛЕНО: НЕ СОЗДАЁМ НОВЫЕ СООБЩЕНИЯ!
            try:
                await message.delete()
            except TelegramBadRequest:
                pass
            msg = await message.bot.send_message(
                chat_id=message.chat.id,
                text=text,
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )
            await state.update_data(last_bot_message_id=msg.message_id)
    else:
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        
        # Редактируем предыдущее сообщение бота
        data_msg = await state.get_data()
        if "last_bot_message_id" in data_msg:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data_msg["last_bot_message_id"],
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
            except Exception:
                msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
                await state.update_data(last_bot_message_id=msg.message_id)
        else:
            msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=msg.message_id)
    
    await state.set_state(CheckoutStates.choosing_payment_method)


# ===== ШАГ 5: ВЫБОР СПОСОБА ОПЛАТЫ =====
@router.callback_query(F.data.startswith("payment:"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор способа оплаты"""
    method = callback.data.split(":")[1]
    
    if method == "online":
        await callback.answer("🚧 Онлайн-оплата пока в разработке", show_alert=True)
        return
    
    await state.update_data(payment_method=method)
    
    # ✅ ЕСЛИ НАЛИЧНЫЕ - СПРАШИВАЕМ ПРО СДАЧУ
    if method == "cash":
        text = "💵 Нужна сдача?\n\nВыберите вариант:"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Без сдачи", callback_data="change:no")
        kb.button(text="💰 Нужна сдача", callback_data="change:yes")
        kb.button(text="❌ Отменить", callback_data="cancel_checkout")
        kb.adjust(2, 1)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await state.update_data(last_bot_message_id=callback.message.message_id)
        await state.set_state(CheckoutStates.choosing_change)
        await callback.answer()
        return
    
    # ✅ ЕСЛИ КАРТОЙ - СРАЗУ К КОММЕНТАРИЮ
    text = "💬 Хотите добавить комментарий к заказу?\n\n"
    text += "Например: \"Позвоните за 30 минут\" или \"Домофон не работает\"\n\n"
    text += "Можете пропустить этот шаг."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_comment)
    await callback.answer()


# ===== Обработчик сдачи =====
@router.callback_query(F.data.startswith("change:"))
async def process_change(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор сдачи"""
    choice = callback.data.split(":")[1]
    
    if choice == "yes":
        # ✅ ИНЛАЙН КНОПКИ С КУПЮРАМИ!
        text = "💰 С какой купюры нужна сдача?\n\nВыберите номинал:"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🟢 1000 ₽", callback_data="bill:1000")
        kb.button(text="🔵 2000 ₽", callback_data="bill:2000")
        kb.button(text="🔴 5000 ₽", callback_data="bill:5000")
        kb.button(text="❌ Отменить", callback_data="cancel_checkout")
        kb.adjust(3, 1)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await state.update_data(change_needed=True, last_bot_message_id=callback.message.message_id)
        await state.set_state(CheckoutStates.choosing_change)
        await callback.answer()
    else:
        # Без сдачи
        await state.update_data(change_needed=False, change_amount=None)
        
        # Переходим к комментарию
        text = "💬 Хотите добавить комментарий к заказу?\n\n"
        text += "Например: \"Позвоните за 30 минут\" или \"Домофон не работает\"\n\n"
        text += "Можете пропустить этот шаг."
        
        kb = InlineKeyboardBuilder()
        kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
        kb.button(text="❌ Отменить", callback_data="cancel_checkout")
        kb.adjust(1)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await state.update_data(last_bot_message_id=callback.message.message_id)
        await state.set_state(CheckoutStates.waiting_for_comment)
        await callback.answer()


# ===== ШАГ 6: КОММЕНТАРИЙ (опционально) =====
@router.callback_query(F.data.startswith("bill:"))
async def process_bill_choice(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор купюры"""
    amount = int(callback.data.split(":")[1])
    await state.update_data(change_amount=amount)
    
    # ✅ Переходим к комментарию
    text = "💬 Хотите добавить комментарий к заказу?\n\n"
    text += "Например: \"Позвоните за 30 минут\" или \"Домофон не работает\"\n\n"
    text += "Можете пропустить этот шаг."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_comment)
    await callback.answer()


@router.message(CheckoutStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработать комментарий к заказу"""
    comment = message.text.strip()
    await state.update_data(comment=comment)
    
    await show_order_confirmation(message, state, from_callback=False)



@router.callback_query(F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропустить комментарий"""
    await state.update_data(comment=None)
    await show_order_confirmation(callback.message, state, from_callback=True)
    await callback.answer()


# ===== ШАГ 7: ПОДТВЕРЖДЕНИЕ ЗАКАЗА =====
async def show_order_confirmation(message: Message, state: FSMContext, from_callback=True):
    """Подтверждение заказа"""
    data = await state.get_data()
    
    # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ КОРЗИНЫ
    cart_items = data.get('cart_items')
    if not cart_items:
        # Получаем из БД
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        cart_items = await get_cart_db(user_id)
        if not cart_items:
            text = "❌ Корзина пуста!"
            if from_callback:
                await message.edit_text(text, parse_mode="HTML")
            else:
                await message.answer(text)
            return
        # Сохраняем в state
        await state.update_data(cart_items=cart_items)
    
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    
    text = "📋 Проверьте заказ:\n━━━━━━━━━━━━━━━━\n\n"
    
    # Товары
    text += "🛒 Товары:\n"
    for i, item in enumerate(cart_items, 1):
        emoji = get_product_emoji(item["product_code"])
        product = await get_product_by_code(item["product_code"])
        if product:
            is_weighted = product[4]
            item_total = item["price"] * item["quantity"]
            if is_weighted:
                text += f"{i}. {emoji} {item['name']}: {item['quantity']} кг × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
            else:
                text += f"{i}. {emoji} {item['name']}: {int(item['quantity'])} шт × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
    
    text += f"\n💰 Итого: {int(total)} ₽\n\n━━━━━━━━━━━━━━━━\n\n"
    text += f"👤 {data.get('customer_name', 'Не указано')}\n📞 {data.get('customer_phone', 'Не указан')}\n\n"
    
    if data.get('delivery_method') == 'delivery':
        text += f"🚚 Доставка\n📍 {data.get('delivery_address', 'Не указан')}\n\n"
    else:
        text += f"🏃 Самовывоз\n📍 {PICKUP_ADDRESS}\n\n"
    
    payment_text = {'cash': '💵 Наличные', 'card': '💳 Картой'}
    text += f"💳 {payment_text.get(data.get('payment_method', 'cash'), '💵 Наличные')}\n\n"
    
    if data.get('payment_method') == 'cash':
        if data.get('change_needed'):
            text += f"💰 Сдача с {data.get('change_amount', 0)} ₽\n"
        else:
            text += "✅ Без сдачи\n"
        text += "\n"
    
    if data.get('comment'):
        text += f"💬 {data['comment']}\n\n"
    
    text += "━━━━━━━━━━━━━━━━\n✅ Всё верно?"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_order")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    # ✅ ИСПРАВЛЕНО: ВСЕГДА РЕДАКТИРУЕМ ПОСЛЕДНЕЕ СООБЩЕНИЕ БОТА!
    if from_callback:
        # Если вызвано из callback (пропустить комментарий)
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        except Exception:
            msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=msg.message_id)
    else:
        # Если вызвано из текстового сообщения (ввод комментария)
        # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        
        # ✅ РЕДАКТИРУЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ БОТА
        data_msg = await state.get_data()
        if 'last_bot_message_id' in data_msg:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data_msg['last_bot_message_id'],
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
            except Exception:
                msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
                await state.update_data(last_bot_message_id=msg.message_id)
        else:
            msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
            await state.update_data(last_bot_message_id=msg.message_id)
    
    await state.set_state(CheckoutStates.confirming_order)



# ===== ШАГ 8: СОХРАНЕНИЕ ЗАКАЗА =====
@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтвердить и сохранить заказ"""
    user_id = callback.from_user.id
    data = await state.get_data()
    
    # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ КОРЗИНЫ
    cart_items = data.get('cart_items')
    if not cart_items:
        cart_items = await get_cart_db(user_id)
        if not cart_items:
            await callback.answer("❌ Корзина пуста!", show_alert=True)
            return
    
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    
    # ✅ СОХРАНЯЕМ/ОБНОВЛЯЕМ ПРОФИЛЬ (ВСЕГДА!)
    profile_data = {
        'full_name': data.get('customer_name', ''),
        'phone': data.get('customer_phone', ''),
        'city': 'Смоленск',
        'street': data.get('delivery_address', ''),
        'house': '',
        'flat': '',
        'entrance': '',
        'floor': '',
        'delivery_type': data.get('delivery_method', 'pickup')
    }

    await upsert_user_profile(user_id, profile_data)
    
    # Сохраняем заказ в БД
    order_data = {
        'customer_name': data.get('customer_name', ''),
        'customer_phone': data.get('customer_phone', ''),
        'delivery_method': data.get('delivery_method', 'pickup'),
        'delivery_address': data.get('delivery_address', ''),
        'payment_method': data.get('payment_method', 'cash'),
        'items': cart_items,
        'total_amount': total,
        'comment': data.get('comment', ''),
        'change_needed': data.get('change_needed', False),
        'change_amount': data.get('change_amount', 0)
    }
    
    order_number = await save_order(user_id, order_data)
    
    # Очищаем корзину
    await clear_cart_db(user_id)
    
    # Уведомление клиенту
    text = "🎉 Заказ успешно оформлен!\n\n"
    text += f"📦 Номер заказа: {order_number}\n"
    text += f"💰 Сумма: {int(total)} ₽\n\n"
    text += "✅ Мы свяжемся с вами в ближайшее время!\n\n"
    text += "📱 Следите за статусом в разделе \"Мои заказы\""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Мои заказы", callback_data="orders")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    # ✅ УВЕДОМЛЕНИЕ АДМИНУ
    await notify_admin_new_order(callback.bot, order_number, order_data, total)
    
    # Очищаем state
    await state.clear()
    await callback.answer("🎊 Спасибо за заказ!", show_alert=False)


async def notify_admin_new_order(bot, order_number: str, order_data: dict, total: float):
    """Отправить уведомление админу о новом заказе"""
    text = "🔔 НОВЫЙ ЗАКАЗ!\n\n"
    text += f"📦 Номер: {order_number}\n"
    text += f"💰 Сумма: {int(total)} ₽\n\n"
    text += f"👤 Клиент: {order_data['customer_name']}\n"
    text += f"📞 Телефон: {order_data['customer_phone']}\n\n"
    
    if order_data['delivery_method'] == 'delivery':
        text += f"🚚 Доставка\n"
        text += f"📍 {order_data['delivery_address']}\n\n"
    else:
        text += "🏃 Самовывоз\n\n"
    
    payment_methods = {
        'cash': '💵 Наличные',
        'card': '💳 Картой',
        'online': '🌐 Онлайн'
    }
    text += f"💳 {payment_methods[order_data['payment_method']]}\n\n"
    
    text += "🛒 Товары:\n"
    for item in order_data['items']:
        emoji = get_product_emoji(item["product_code"])
        text += f"• {emoji} {item['name']}: {item['quantity']} × {int(item['price'])} ₽\n"
    
    if order_data.get('comment'):
        text += f"\n💬 Комментарий: {order_data['comment']}"
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def ask_order_comment(callback: CallbackQuery, state: FSMContext):
    """Спросить комментарий к заказу (после callback)"""
    text = "💬 Добавить комментарий к заказу?\n\n"
    text += "Например: позвоните за 10 минут, домофон не работает"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_comment)
    await callback.answer()


async def ask_order_comment_message(message: Message, state: FSMContext):
    """Спросить комментарий к заказу (после текстового ввода)"""
    text = "💬 Добавить комментарий к заказу?\n\n"
    text += "Например: позвоните за 10 минут, домофон не работает"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(CheckoutStates.waiting_for_comment)


# ===== ОТМЕНА ОФОРМЛЕНИЯ =====
@router.callback_query(F.data == "cancel_checkout")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    """Отменить оформление заказа"""
    await state.clear()
    
    text = "❌ Оформление заказа отменено\n\n"
    text += "Ваша корзина сохранена. Вы можете вернуться к покупкам."
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Корзина", callback_data="cart")
    kb.button(text="🛍️ Каталог", callback_data="catalog")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await callback.answer()


# ======= Обработчик выбора адреса ======
@router.callback_query(F.data == "choose_delivery_address")
async def choose_delivery_address(callback: CallbackQuery, state: FSMContext):
    """Выбрать адрес доставки"""
    user_id = callback.from_user.id
    addresses = await get_user_addresses(user_id)
    
    text = "📍 Выберите адрес доставки:\n\n"
    kb = InlineKeyboardBuilder()
    
    for addr in addresses:
        default_mark = "⭐ " if addr['is_default'] else ""
        text += f"• {default_mark}{addr['label']}\n"
        text += f"   {addr['address']}\n\n"
        kb.button(
            text=f"{default_mark}{addr['label']}",
            callback_data=f"select_delivery_address:{addr['id']}"
        )
    
    kb.button(text="➕ Ввести новый адрес", callback_data="enter_new_delivery_address")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("select_delivery_address:"))
async def select_delivery_address(callback: CallbackQuery, state: FSMContext):
    """Выбрать адрес доставки"""
    addr_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Получаем адрес
    addresses = await get_user_addresses(user_id)
    selected_addr = next((addr for addr in addresses if addr['id'] == addr_id), None)
    
    if not selected_addr:
        await callback.answer("❌ Адрес не найден!")
        return
    
    # Сохраняем в state
    await state.update_data(delivery_address=selected_addr['address'])
    await callback.answer(f"✅ Выбран: {selected_addr['label']}")
    
    # Переходим к следующему шагу
    await ask_payment_method(callback.message, state, edit=True)


# ===== Обработчик "Ввести новый адрес" =====
@router.callback_query(F.data == "enter_new_delivery_address")
async def enter_new_delivery_address(callback: CallbackQuery, state: FSMContext):
    """Ввести новый адрес доставки"""
    text = "📍 Введите адрес доставки:\n\n"
    text += "Пример: г. Смоленск, ул. Ленина, д. 10, кв. 5"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(CheckoutStates.waiting_for_address)
    await callback.answer()
