import logging
import re
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import ProfileStates 
from bot.states import CheckoutStates 
# Импорты из проекта
from bot.db_postgres import (
    get_categories,
    get_products_by_category,
    get_product_by_code,
    add_to_cart_db,
    get_cart_db,
    clear_cart_db,
    remove_item_from_cart_db,
    get_user_profile,
    get_user_orders,
    save_user_profile,
    upsert_user_profile,
    update_user_profile,
    get_user_addresses,
    add_user_address,
    delete_user_address,
    set_default_address,
    get_default_address
)

logger = logging.getLogger(__name__)
router = Router()

# ID администраторов
ADMIN_IDS = {878283648}  # Замени на свой!


# ===== ЭМОДЗИ ДЛЯ КАТЕГОРИЙ =====
CATEGORY_EMOJI = {
    "fresh_fish": "🐟",          # Свежая рыба
    "frozen": "❄️",              # Замороженное
    "smoked": "🔥",              # Копчёное
    "delicacy": "⭐",            # Деликатесы
    "caviar": "🍣",              # Икра
    "shellfish": "🦞",           # Морепродукты
    "seafood": "🦞",             # Морепродукты (альтернативное название)
}

# ===== ЭМОДЗИ ДЛЯ ТОВАРОВ (по коду или ключевым словам) =====
PRODUCT_EMOJI = {
    # Рыба
    "salmon": "🐟",              # Лосось
    "seabass": "🐠",            # Сибас
    "trout": "🐋",              # Форель
    "tuna": "🦈",               # Тунец
    "dorado": "🐠",             # Дорадо
    "herring": "🐟",            # Сельдь
    "mackerel": "🐟",           # Скумбрия
    "cod": "🐟",                # Треска
    
    # Морепродукты
    "shrimp": "🦐",             # Креветки
    "prawn": "🦐",              # Креветки тигровые
    "crab": "🦀",               # Краб
    "lobster": "🦞",            # Лобстер
    "squid": "🦑",              # Кальмар
    "octopus": "🐙",            # Осьминог
    "oyster": "🦪",             # Устрицы
    "mussel": "🦪",             # Мидии
    "scallop": "🦪",            # Гребешки
    
    # Икра
    "red_caviar": "🔴",         # Красная икра
    "black_caviar": "⚫",       # Чёрная икра
    "caviar": "🔴⚫",           # Икра общая
    
    # Копчёное
    "smoked_salmon": "🔥💥",    # Копчёный лосось
    "smoked": "🔥💥",           # Копчёное
}


def get_product_emoji(prod_code: str) -> str:
    """Получить эмодзи для товара по коду"""
    # Сначала ищем точное совпадение
    if prod_code in PRODUCT_EMOJI:
        return PRODUCT_EMOJI[prod_code]
    
    # Если не нашли, ищем по ключевым словам
    prod_lower = prod_code.lower()
    
    # Икра
    if "caviar" in prod_lower or "икра" in prod_lower:
        if "red" in prod_lower or "красн" in prod_lower:
            return "🔴"
        elif "black" in prod_lower or "черн" in prod_lower:
            return "⚫"
        return "🔴⚫"
    
    # Морепродукты
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
    
    # Рыба (по умолчанию)
    return "🐟"


def get_category_emoji(cat_code: str) -> str:
    """Получить эмодзи для категории"""
    return CATEGORY_EMOJI.get(cat_code, "🐟")


# ===== ГЛАВНОЕ МЕНЮ =====

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start - показать главное меню"""
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    is_premium = message.from_user.is_premium
    
    logger.info(f"👤 User ID: {user_id}, Username: @{username}, Premium: {is_premium}")
    
    # ✅ КРАСИВОЕ ПРИВЕТСТВИЕ (для премиум - с анимацией)
    if is_premium:
        text = "🌊✨ <b>Добро пожаловать в Шеф Порт!</b> ✨🐟\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎉🛳⚓️ <i>VIP-клиент!</i> Для вас особые условия! 🎁\n\n"
    else:
        text = "🌊 <b>Добро пожаловать в Шеф Порт!</b> 🐟\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if user_id in ADMIN_IDS:
        text += "🔧 <i>Режим администратора</i>\n"
        text += f"🆔 ID: <code>{user_id}</code>\n\n"
    
    text += "📋 Выберите действие из меню ниже:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ Каталог товаров", callback_data="catalog")
    kb.button(text="🌐 Открыть каталог", web_app=WebAppInfo(url="https://chefport-mini.ru"))
    kb.button(text="🛒 Моя корзина", callback_data="cart")
    kb.button(text="📦 Мои заказы", callback_data="orders")
    kb.button(text="😜 Профиль", callback_data="profile")
    kb.button(text="📞 Контакты", callback_data="contacts")
    kb.button(text="ℹ️ Информация", callback_data="info")
    kb.adjust(2)
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нечего отменять")
        return
    
    await state.clear()
    await message.answer("✅ Операция отменена. Используйте /start для возврата в меню.")


# ===== CALLBACK: ГЛАВНОЕ МЕНЮ =====

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    text = "🌊 <b>Шеф Порт</b> 🐟\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📋 Выберите действие:"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ Каталог товаров", callback_data="catalog")
    kb.button(text="🌐 Открыть каталог", web_app=WebAppInfo(url="https://chefport-mini.ru"))
    kb.button(text="🛒 Моя корзина", callback_data="cart")
    kb.button(text="📦 Мои заказы", callback_data="orders")
    kb.button(text="😜 Профиль", callback_data="profile")
    kb.button(text="📞 Контакты", callback_data="contacts")
    kb.button(text="ℹ️ Информация", callback_data="info")
    kb.adjust(2)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# ===== КАТАЛОГ =====

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать каталог категорий"""
    categories = await get_categories()
    
    if not categories:
        await callback.answer("❌ Каталог пуст", show_alert=True)
        return
    
    # ✅ ПОКАЗЫВАЕМ КОРЗИНУ СВЕРХУ
    cart_items = await get_cart_db(callback.from_user.id)
    
    if not cart_items:
        cart_summary = "🛒 <b>Корзина пуста</b>"
    else:
        total = sum(item["price"] * item["quantity"] for item in cart_items)
        cart_summary = "🛒 <b>В корзине:</b>\n"
        
        for item in cart_items:
            emoji = get_product_emoji(item["product_code"])
            product = await get_product_by_code(item["product_code"])
            
            if product:
                is_weighted = product[4]
                item_total = item["price"] * item["quantity"]
                
                if is_weighted:
                    cart_summary += f"{emoji} {item['name']}: {item['quantity']} кг × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
                else:
                    cart_summary += f"{emoji} {item['name']}: {int(item['quantity'])} шт × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
        
        cart_summary += f"\n💰 <b>Итого: {int(total)} ₽</b>"
    
    text = "🛍️ <b>Каталог товаров</b>\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    text += cart_summary + "\n\n"
    text += "━━━━━━━━━━━━━━━━\n"
    text += "📂 Выберите категорию:"
    
    kb = InlineKeyboardBuilder()
    
    # Кнопки категорий
    for cat in categories:
        cat_id, cat_code, cat_name, _ = cat
        emoji = get_category_emoji(cat_code)
        kb.button(text=f"{emoji} {cat_name}", callback_data=f"category:{cat_code}")
    
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(2)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery):
    """Показать товары категории"""
    cat_code = callback.data.split(":")[1]
    products = await get_products_by_category(cat_code)
    
    if not products:
        await callback.answer("❌ В этой категории пока нет товаров", show_alert=True)
        return
    
    # Название категории
    categories = await get_categories()
    cat_name = next((name for _, code, name, _ in categories if code == cat_code), "Товары")
    cat_emoji = get_category_emoji(cat_code)
    
    # ✅ ПОКАЗЫВАЕМ КОРЗИНУ СВЕРХУ
    cart_items = await get_cart_db(callback.from_user.id)
    
    if not cart_items:
        cart_summary = "🛒 <b>Корзина пуста</b>"
    else:
        total = sum(item["price"] * item["quantity"] for item in cart_items)
        cart_summary = "🛒 <b>В корзине:</b>\n"
        
        for item in cart_items:
            emoji = get_product_emoji(item["product_code"])
            product = await get_product_by_code(item["product_code"])
            
            if product:
                is_weighted = product[4]
                item_total = item["price"] * item["quantity"]
                
                if is_weighted:
                    cart_summary += f"{emoji} {item['name']}: {item['quantity']} кг × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
                else:
                    cart_summary += f"{emoji} {item['name']}: {int(item['quantity'])} шт × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
        
        cart_summary += f"\n💰 <b>Итого: {int(total)} ₽</b>"
    
    text = f"{cat_emoji} <b>{cat_name}</b>\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    text += cart_summary + "\n\n"
    text += "━━━━━━━━━━━━━━━━\n"
    text += "Выберите товар:"
    
    kb = InlineKeyboardBuilder()
    
    # Кнопки товаров
    for prod in products:
        prod_id, _, prod_code, prod_name, price_per_kg, is_weighted, _, _ = prod
        
        emoji = get_product_emoji(prod_code)
        
        if is_weighted:
            price_text = f"{emoji} {prod_name} — {int(price_per_kg)} ₽/кг"
        else:
            price_text = f"{emoji} {prod_name} — {int(price_per_kg)} ₽/шт"
        
        kb.button(text=price_text, callback_data=f"product:{prod_code}")
    
    kb.button(text="◀️ Каталог", callback_data="catalog")
    kb.adjust(1)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детали товара"""
    prod_code = callback.data.split(":")[1]
    product = await get_product_by_code(prod_code)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    prod_id, cat_id, prod_name, price_per_kg, is_weighted, min_weight_kg, description = product
    
    # Получаем текущее количество в корзине
    cart_items = await get_cart_db(callback.from_user.id)
    current_qty = 0
    
    for item in cart_items:
        if item["product_code"] == prod_code:
            current_qty = item["quantity"]
            break
    
    # ✅ ЭМОДЗИ ДЛЯ ТОВАРА
    emoji = get_product_emoji(prod_code)
    
    # ✅ ПОКАЗЫВАЕМ КОРЗИНУ СВЕРХУ
    if not cart_items:
        cart_summary = "🛒 <b>Корзина пуста</b>"
    else:
        total = sum(item["price"] * item["quantity"] for item in cart_items)
        cart_summary = "🛒 <b>В корзине:</b>\n"
        
        for item in cart_items:
            item_emoji = get_product_emoji(item["product_code"])
            item_product = await get_product_by_code(item["product_code"])
            
            if item_product:
                item_is_weighted = item_product[4]
                item_total = item["price"] * item["quantity"]
                
                if item_is_weighted:
                    cart_summary += f"{item_emoji} {item['name']}: {item['quantity']} кг × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
                else:
                    cart_summary += f"{item_emoji} {item['name']}: {int(item['quantity'])} шт × {int(item['price'])} ₽ = {int(item_total)} ₽\n"
        
        cart_summary += f"\n💰 <b>Итого: {int(total)} ₽</b>"
    
    # ✅ КРАСИВОЕ ОФОРМЛЕНИЕ
    text = cart_summary + "\n\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    text += f"{emoji} <b>{prod_name}</b> {emoji}\n\n"
    
    if description:
        text += f"📝 {description}\n\n"
    
    # Правильное отображение для весовых и штучных товаров
    if is_weighted:
        text += f"💰 Цена: <b>{int(price_per_kg)} ₽/кг</b>\n"
        text += f"⚖️ Минимум: {min_weight_kg} кг\n\n"
        
        if current_qty > 0:
            total_price = current_qty * price_per_kg
            text += f"✅ <b>Этого товара в корзине:</b>\n"
            text += f"   {current_qty} кг × {int(price_per_kg)} ₽ = <b>{int(total_price)} ₽</b>"
    else:
        text += f"💰 Цена: <b>{int(price_per_kg)} ₽/шт</b>\n\n"
        
        if current_qty > 0:
            total_price = current_qty * price_per_kg
            text += f"✅ <b>Этого товара в корзине:</b>\n"
            text += f"   {int(current_qty)} шт × {int(price_per_kg)} ₽ = <b>{int(total_price)} ₽</b>"
    
    kb = InlineKeyboardBuilder()
    
    # ✅ РЯД 1-2: КНОПКИ УПРАВЛЕНИЯ (минусы и плюсы)
    if is_weighted:
        # Кнопки МИНУС (серебряные стрелки вниз ⬇️)
        if current_qty >= 0.1:
            kb.button(text="⬇️ 0.1 кг", callback_data=f"sub:{prod_code}:0.1")
        if current_qty >= 0.5:
            kb.button(text="⬇️ 0.5 кг", callback_data=f"sub:{prod_code}:0.5")
        if current_qty >= 1:
            kb.button(text="⬇️ 1 кг", callback_data=f"sub:{prod_code}:01")
       
        # Кнопки ПЛЮС (золотые стрелки вверх ⛏️)
        kb.button(text="⛏️ 0.1 кг", callback_data=f"add:{prod_code}:0.1")
        kb.button(text="⛏️ 0.5 кг", callback_data=f"add:{prod_code}:0.5")
        kb.button(text="⛏️ 1 кг", callback_data=f"add:{prod_code}:1")
        
    else:
        # Штучные товары
        # Кнопки МИНУС
        if current_qty >= 1:
            kb.button(text="⬇️ 1 шт", callback_data=f"sub:{prod_code}:1")
        
        # Кнопки ПЛЮС
        kb.button(text="⛏️ 1 шт", callback_data=f"add:{prod_code}:1")
        kb.button(text="⛏️ 2 шт", callback_data=f"add:{prod_code}:2")
    
    # ✅ РЯД 3: НАВИГАЦИЯ (3 кнопки)
    categories = await get_categories()
    cat_code = None
    for c_id, c_code, _, _ in categories:
        if c_id == cat_id:
            cat_code = c_code
            break
    
    kb.button(text="◀️ Назад", callback_data=f"category:{cat_code}")
    kb.button(text="🛍️ Каталог", callback_data="catalog")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    
    # ✅ РЯД 4: ДЕЙСТВИЯ (2 кнопки)
    if cart_items:
        kb.button(text="✅ Оформить заказ", callback_data="checkout")
    kb.button(text="🛒 Корзина", callback_data="cart")
    
    # ✅ ПРАВИЛЬНОЕ РАСПОЛОЖЕНИЕ РЯДОВ
    if is_weighted:
        minus_count = 0
        if current_qty >= 1:
            minus_count += 1
        if current_qty >= 0.5:
            minus_count += 1
        if current_qty >= 0.1:
            minus_count += 1
        
        if minus_count > 0:
            kb.adjust(minus_count, 3, 3, 2)  # минусы, плюсы, навигация, действия
        else:
            kb.adjust(3, 3, 2)  # плюсы, навигация, действия
    else:
        if current_qty >= 1:
            kb.adjust(1, 2, 3, 2)  # минус, плюсы, навигация, действия
        else:
            kb.adjust(2, 3, 2)  # плюсы, навигация, действия
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    parts = callback.data.split(":")
    prod_code = parts[1]
    quantity = float(parts[2])
    
    user_id = callback.from_user.id
    is_premium = callback.from_user.is_premium
    
    # Добавляем в корзину
    await add_to_cart_db(user_id, prod_code, quantity)
    
    # ✅ АНИМИРОВАННОЕ УВЕДОМЛЕНИЕ (для Premium - с эффектами)
    emoji = get_product_emoji(prod_code)
    
    if is_premium:
        # Для премиум - с анимированными эмодзи
        await callback.answer(f"✨ {emoji} +{quantity} ✨ Добавлено!", show_alert=False)
    else:
        # Для обычных - простое
        await callback.answer(f"{emoji} ✅ Добавлено +{quantity}", show_alert=False)
    
    # Автоматически обновляем карточку товара
    await show_product_detail(callback)


@router.callback_query(F.data.startswith("sub:"))
async def subtract_from_cart(callback: CallbackQuery):
    """Уменьшить количество товара в корзине"""
    parts = callback.data.split(":")
    prod_code = parts[1]
    quantity = float(parts[2])
    
    user_id = callback.from_user.id
    
    # Уменьшаем количество (отрицательное значение)
    await add_to_cart_db(user_id, prod_code, -quantity)
    
    # Уведомление
    emoji = get_product_emoji(prod_code)
    await callback.answer(f"{emoji} ➖ Убрано -{quantity}", show_alert=False)
    
    # Автоматически обновляем карточку товара
    await show_product_detail(callback)


# ===== КОРЗИНА =====

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Показать корзину"""
    user_id = callback.from_user.id
    cart_items = await get_cart_db(user_id)
    
    if not cart_items:
        text = "🛒 <b>Ваша корзина пуста</b>\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
        text += "😔 Добавьте товары из каталога!"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🛍️ Перейти в каталог", callback_data="catalog")
        kb.button(text="◀️ Главное меню", callback_data="main_menu")
        kb.adjust(1)
    else:
        total = sum(item["price"] * item["quantity"] for item in cart_items)
        
        text = "🛒 <b>Ваша корзина</b>\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
        
        # ✅ Показываем все товары с ЭМОДЗИ
        for i, item in enumerate(cart_items, 1):
            product = await get_product_by_code(item["product_code"])
            if product:
                is_weighted = product[4]
                emoji = get_product_emoji(item["product_code"])
                
                if is_weighted:
                    text += f"{i}. {emoji} <b>{item['name']}</b>\n"
                    text += f"   ⚖️ {item['quantity']} кг × {int(item['price'])} ₽ = <b>{int(item['price'] * item['quantity'])} ₽</b>\n\n"
                else:
                    text += f"{i}. {emoji} <b>{item['name']}</b>\n"
                    text += f"   📦 {int(item['quantity'])} шт × {int(item['price'])} ₽ = <b>{int(item['price'] * item['quantity'])} ₽</b>\n\n"
        
        text += "━━━━━━━━━━━━━━━━\n"
        text += f"💰 <b>Итого: {int(total)} ₽</b>"
        
        kb = InlineKeyboardBuilder()
        
        # Кнопки удаления товаров
        for item in cart_items:
            emoji = get_product_emoji(item["product_code"])
            kb.button(
                text=f"🗑 {emoji} {item['name'][:12]}",
                callback_data=f"remove:{item['product_code']}"
            )
        
        kb.button(text="✅ Оформить заказ", callback_data="checkout")
        kb.button(text="🗑 Очистить всё", callback_data="clear_cart")
        kb.button(text="🛍️ Продолжить покупки", callback_data="catalog")
        kb.button(text="◀️ Главное меню", callback_data="main_menu")
        kb.adjust(2, 1, 1, 1, 1)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    prod_code = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    await remove_item_from_cart_db(user_id, prod_code)
    
    emoji = get_product_emoji(prod_code)
    await callback.answer(f"{emoji} 🗑 Товар удалён из корзины")
    
    # Обновляем корзину
    await show_cart(callback)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    await clear_cart_db(user_id)
    
    await callback.answer("🗑 Корзина полностью очищена!")
    
    # Показываем пустую корзину
    await show_cart(callback)



# ===== ДРУГИЕ РАЗДЕЛЫ =====

@router.callback_query(F.data == "orders")
async def show_orders(callback: CallbackQuery):
    """Показать заказы пользователя"""
    user_id = callback.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        text = "📦 <b>Мои заказы</b>\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
        text += "У вас пока нет заказов.\n"
        text += "Оформите первый заказ из каталога! 🛍️"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🛍️ Каталог", callback_data="catalog")
        kb.button(text="◀️ Главное меню", callback_data="main_menu")
        kb.adjust(1)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await callback.answer()
        return
    
    # Показываем заказы
    text = "📦 <b>Мои заказы</b>\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    status_emoji = {
        'new': '🆕 Новый',
        'confirmed': '✅ Подтверждён',
        'cooking': '👨‍🍳 Готовится',
        'delivering': '🚚 В доставке',
        'ready': '🏃 Готов к выдаче',
        'completed': '🎉 Выполнен',
        'cancelled': '❌ Отменён'
    }
    
    kb = InlineKeyboardBuilder()
    
    for order in orders[:10]:  # Последние 10 заказов
        emoji = status_emoji.get(order['status'], '📦 ' + order['status'])
        order_short = order['order_number'][-12:]  # Последние 12 символов
        
        text += f"{emoji}\n"
        text += f"📋 <code>{order_short}</code>\n"
        text += f"💰 {int(order['total_amount'])} ₽\n"
        text += f"📅 {order['created_at'][:16]}\n\n"
        
        kb.button(
            text=f"📋 {order_short}",
            callback_data=f"order:{order['order_number']}"
        )
    
    kb.button(text="◀️ Главное меню", callback_data="main_menu")
    kb.adjust(2, 2, 2, 2, 2, 1)  # По 2 кнопки в ряд
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# ===== УПРАВЛЕНИЕ АДРЕСАМИ =====

@router.callback_query(F.data == "manage_addresses")
async def manage_addresses(callback: CallbackQuery, state: FSMContext):
    """Управление адресами"""
    user_id = callback.from_user.id
    addresses = await get_user_addresses(user_id)
    
    text = "📍 <b>Мои адреса</b>\n\n"
    
    kb = InlineKeyboardBuilder()
    
    if addresses:
        for i, addr in enumerate(addresses, 1):
            default_mark = "⭐ " if addr['is_default'] else ""
            text += f"{i}. {default_mark}{addr['label']}\n"
            text += f"   {addr['address']}\n\n"
            
            kb.button(text=f"❌ Удалить #{i}", callback_data=f"delete_addr:{addr['id']}")
            if not addr['is_default']:
                kb.button(text=f"⭐ Сделать основным #{i}", callback_data=f"default_addr:{addr['id']}")
        
        kb.adjust(2)
    else:
        text += "У вас пока нет сохранённых адресов."
    
    kb.button(text="➕ Добавить адрес", callback_data="add_address")
    kb.button(text="🔙 Назад", callback_data="profile")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(ProfileStates.managing_addresses)
    await callback.answer()


@router.callback_query(F.data == "add_address")
async def add_address_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление адреса"""
    text = "🏠 <b>Введите новый адрес</b>\n\n"
    text += "Пример: г. Смоленск, ул. Ленина, д. 10, кв. 5, под. 2, этаж 3"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="manage_addresses")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)  # ✅ ДОБАВЬ!
    await state.set_state(ProfileStates.waiting_for_new_address)
    await callback.answer()



@router.message(ProfileStates.waiting_for_new_address)
async def process_new_address(message: Message, state: FSMContext):
    """Обработать новый адрес"""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Попробуйте ещё раз:")
        return
    
    # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    try:
        await message.delete()
    except Exception:
        pass
    
    # ✅ УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ БОТА ("Введите новый адрес")
    data = await state.get_data()
    if 'last_bot_message_id' in data:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['last_bot_message_id']
            )
        except Exception:
            pass
    
    await state.update_data(new_address=address)
    
    text = "🏷️ <b>Дайте название адресу</b>\n\n"
    text += "Например: Дом, Работа, Дача\n\n"
    text += "Или нажмите \"Пропустить\""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_label")
    kb.button(text="❌ Отменить", callback_data="manage_addresses")
    kb.adjust(1)
    
    # ✅ СОХРАНЯЕМ НОВЫЙ message_id
    msg = await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=msg.message_id)
    
    await state.set_state(ProfileStates.waiting_for_address_label)




@router.message(ProfileStates.waiting_for_address_label)
async def process_address_label(message: Message, state: FSMContext):
    """Обработать метку адреса"""
    label = message.text.strip()
    data = await state.get_data()
    user_id = message.from_user.id
    
    # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    try:
        await message.delete()
    except Exception:
        pass
    
    # ✅ УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ БОТА (про метку)
    if 'last_bot_message_id' in data:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['last_bot_message_id']
            )
        except Exception:
            pass
    
    addresses = await get_user_addresses(user_id)
    is_first = len(addresses) == 0
    
    await add_user_address(user_id, data['new_address'], label, is_default=is_first)
    
    await state.clear()
    
    # ✅ ПОКАЗЫВАЕМ "МОИ АДРЕСА" ЧЕРЕЗ НОВОЕ СООБЩЕНИЕ
    text = "📍 <b>Мои адреса</b>\n\n"
    kb = InlineKeyboardBuilder()
    
    # Обновляем список адресов
    addresses = await get_user_addresses(user_id)
    
    if addresses:
        for i, addr in enumerate(addresses, 1):
            default_mark = "⭐ " if addr['is_default'] else ""
            text += f"{i}. {default_mark}{addr['label']}\n"
            text += f"   {addr['address']}\n\n"
            
            kb.button(text=f"🗑️ {i}", callback_data=f"delete_addr:{addr['id']}")
            if not addr['is_default']:
                kb.button(text=f"⭐ {i}", callback_data=f"default_addr:{addr['id']}")
        
        kb.adjust(2)
    else:
        text += "У вас нет сохранённых адресов.\n"
    
    kb.button(text="➕ Добавить адрес", callback_data="add_address")
    kb.button(text="◀️ Профиль", callback_data="profile")
    kb.adjust(1)
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())




@router.callback_query(F.data == "skip_label")
async def skip_label(callback: CallbackQuery, state: FSMContext):
    """Пропустить метку"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    addresses = await get_user_addresses(user_id)
    is_first = len(addresses) == 0
    
    await add_user_address(user_id, data['new_address'], "Адрес", is_default=is_first)
    
    await state.clear()
    await callback.answer("✅ Адрес сохранён!")
    
    # ✅ ПОКАЗЫВАЕМ "МОИ АДРЕСА"
    await manage_addresses(callback, state)





@router.callback_query(F.data.startswith("delete_addr:"))
async def delete_address(callback: CallbackQuery, state: FSMContext):
    """Удалить адрес"""
    addr_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    await delete_user_address(addr_id, user_id)
    
    await callback.answer("✅ Адрес удалён!")
    await manage_addresses(callback, state)


@router.callback_query(F.data.startswith("default_addr:"))
async def set_default(callback: CallbackQuery, state: FSMContext):
    """Установить основной адрес"""
    addr_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    await set_default_address(addr_id, user_id)
    
    await callback.answer("✅ Адрес установлен как основной!")
    await manage_addresses(callback, state)


# ===== ПРОФИЛЬ (ДОБАВЬ В КОНЕЦ ФАЙЛА) =====

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    addresses = await get_user_addresses(user_id)
    
    if not profile:
        text = "📝 <b>У вас ещё нет профиля</b>\n\n"
        text += "Профиль создаётся автоматически при первом заказе."
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🏠 Главное меню", callback_data="main_menu")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        await callback.answer()
        return
    
    # Показываем профиль
    text = "👤 <b>Мой профиль</b>\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    text += f"📝 ФИО: {profile.get('full_name', 'Не указано')}\n"
    text += f"📞 Телефон: {profile.get('phone', 'Не указан')}\n"
    text += f"🏙️ Город: {profile.get('city', 'Не указан')}\n\n"
    
    # Адреса
    text += "📍 <b>Мои адреса:</b>\n"
    if addresses:
        for i, addr in enumerate(addresses, 1):
            default_mark = "⭐ " if addr['is_default'] else ""
            text += f"{i}. {default_mark}{addr['label']}\n"
            text += f"   {addr['address']}\n"
    else:
        text += "Адреса не добавлены\n"
    
    text += "\n━━━━━━━━━━━━━━━━"
    
    # Кнопки
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить имя", callback_data="edit:name")
    kb.button(text="📞 Изменить телефон", callback_data="edit:phone")
    kb.button(text="📍 Мои адреса", callback_data="manage_addresses")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# ===== РЕДАКТИРОВАНИЕ ИМЕНИ =====
@router.callback_query(F.data == "edit:name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    """Изменение имени (только через текст)"""
    text = "✏️ <b>Введите новое имя:</b>"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="profile")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(ProfileStates.editing_name)
    await callback.answer()



@router.message(ProfileStates.editing_name)
async def process_new_name(message: Message, state: FSMContext):
    """Обработать новое имя"""
    new_name = message.text.strip()
    user_id = message.from_user.id
    
    if len(new_name) < 2:
        await message.answer("❌ Имя слишком короткое. Попробуйте ещё раз:")
        return
    
    # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    try:
        await message.delete()
    except Exception:
        pass
    
    profile = await get_user_profile(user_id)
    
    if profile:
        profile['full_name'] = new_name
        await upsert_user_profile(user_id, profile)
        
        # ✅ РЕДАКТИРУЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ
        data = await state.get_data()
        if 'last_bot_message_id' in data:
            try:
                text = f"👤 <b>Мой профиль</b>\n\n"
                text += f"📝 ФИО: {profile['full_name']}\n"
                text += f"📞 Телефон: {profile.get('phone', 'Не указан')}\n"
                text += f"🏙️ Город: {profile.get('city', 'Не указан')}\n\n"
                
                addresses = await get_user_addresses(user_id)
                text += "📍 <b>Мои адреса:</b>\n"
                if addresses:
                    for i, addr in enumerate(addresses, 1):
                        default_mark = "⭐ " if addr['is_default'] else ""
                        text += f"{i}. {default_mark}{addr['label']}\n"
                        text += f"   {addr['address']}\n"
                else:
                    text += "Адреса не добавлены\n"
                
                text += "\n━━━━━━━━━━━━━━━━"
                
                kb = InlineKeyboardBuilder()
                kb.button(text="✏️ Изменить имя", callback_data="edit:name")
                kb.button(text="📞 Изменить телефон", callback_data="edit:phone")
                kb.button(text="📍 Мои адреса", callback_data="manage_addresses")
                kb.button(text="🏠 Главное меню", callback_data="main_menu")
                kb.adjust(2, 1, 1)
                
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data['last_bot_message_id'],
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
            except Exception:
                # Если не получилось редактировать
                await message.answer("✅ Имя обновлено!")
        
        await state.clear()
    else:
        await message.answer("❌ Профиль не найден!")
        await state.clear()





# ===== РЕДАКТИРОВАНИЕ ТЕЛЕФОНА =====
@router.callback_query(F.data == "edit:phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование телефона"""
    text = "📞 <b>Введите новый номер телефона:</b>\n\n"
    text += "Формат: +7 (XXX) XXX-XX-XX или 89XXXXXXXXX"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="profile")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(ProfileStates.editing_phone)
    await callback.answer()


@router.message(ProfileStates.editing_phone)
async def process_new_phone(message: Message, state: FSMContext):
    """Обработать новый телефон"""
    phone = message.text.strip()
    user_id = message.from_user.id
    
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # ✅ УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ СРАЗУ (ДО ПРОВЕРКИ!)
    try:
        await message.delete()
    except Exception:
        pass
    
    if not re.match(r'^(\+7|8)\d{10}$', phone_clean):
        # ✅ РЕДАКТИРУЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ БОТА (НЕ СОЗДАЁМ НОВОЕ!)
        data = await state.get_data()
        if 'last_bot_message_id' in data:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data['last_bot_message_id'],
                    text="❌ <b>Неверный формат!</b>\n\n"
                         "Введите номер в формате:\n"
                         "+7 (999) 123-45-67 или 89991234567",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardBuilder()
                        .button(text="❌ Отменить", callback_data="profile")
                        .as_markup()
                )
            except Exception:
                await message.answer(
                    "❌ Неверный формат!\n\n"
                    "Введите номер в формате:\n"
                    "+7 (999) 123-45-67 или 89991234567"
                )
        else:
            await message.answer(
                "❌ Неверный формат!\n\n"
                "Введите номер в формате:\n"
                "+7 (999) 123-45-67 или 89991234567"
            )
        return
    
    if phone_clean.startswith('8'):
        phone_clean = '+7' + phone_clean[1:]
    
    profile = await get_user_profile(user_id)
    
    if profile:
        profile['phone'] = phone_clean
        await upsert_user_profile(user_id, profile)
        
        # ✅ РЕДАКТИРУЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ
        data = await state.get_data()
        if 'last_bot_message_id' in data:
            try:
                text = f"👤 <b>Мой профиль</b>\n\n"
                text += f"📝 ФИО: {profile['full_name']}\n"
                text += f"📞 Телефон: {profile['phone']}\n"
                text += f"🏙️ Город: Смоленск\n\n"
                
                addresses = await get_user_addresses(user_id)
                text += "📍 <b>Мои адреса:</b>\n"
                if addresses:
                    for i, addr in enumerate(addresses, 1):
                        default_mark = "⭐ " if addr['is_default'] else ""
                        text += f"{i}. {default_mark}{addr['label']}\n"
                        text += f"   {addr['address']}\n"
                else:
                    text += "Адреса не добавлены\n"
                
                text += "\n━━━━━━━━━━━━━━━━"
                
                kb = InlineKeyboardBuilder()
                kb.button(text="✏️ Изменить имя", callback_data="edit:name")
                kb.button(text="📞 Изменить телефон", callback_data="edit:phone")
                kb.button(text="📍 Мои адреса", callback_data="manage_addresses")
                kb.button(text="🏠 Главное меню", callback_data="main_menu")
                kb.adjust(2, 1, 1)
                
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data['last_bot_message_id'],
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
            except Exception:
                await message.answer("✅ Телефон обновлён!")
        
        await state.clear()
    else:
        await message.answer("❌ Профиль не найден!")
        await state.clear()




@router.message(ProfileStates.editing_city)
async def process_new_city(message: Message, state: FSMContext):
    """Обработать новый город"""
    new_city = message.text.strip()
    user_id = message.from_user.id
    
    # Обновляем профиль
    profile = await get_user_profile(user_id) or {}
    profile_data = {
        'full_name': profile.get('full_name', ''),
        'phone': profile.get('phone', ''),
        'city': new_city,
        'street': profile.get('street', ''),
        'house': '',
        'flat': '',
        'entrance': '',
        'floor': '',
        'delivery_type': profile.get('delivery_type', 'delivery')
    }
    await upsert_user_profile(user_id, profile_data)
    
    await message.answer("✅ Город обновлён!")
    await state.clear()
    await show_profile_message(message, user_id)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def ask_order_comment(callback: CallbackQuery, state: FSMContext):
    """Спросить комментарий к заказу"""
    text = "💬 <b>Добавить комментарий к заказу?</b>\n\n"
    text += "Например: позвоните за 10 минут, домофон не работает"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="skip_comment")
    kb.button(text="❌ Отменить", callback_data="cancel_checkout")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(CheckoutStates.waiting_for_comment)
    await callback.answer()

async def show_profile_message(message: Message, user_id: int):
    """Показать профиль после обновления"""
    profile = await get_user_profile(user_id)
    addresses = await get_user_addresses(user_id)
    
    text = "👤 <b>Мой профиль</b>\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    text += f"📝 ФИО: {profile.get('full_name', 'Не указано')}\n"
    text += f"📞 Телефон: {profile.get('phone', 'Не указан')}\n"
    text += f"🏙️ Город: {profile.get('city', 'Не указан')}\n\n"
    
    text += "📍 <b>Мои адреса:</b>\n"
    if addresses:
        for i, addr in enumerate(addresses, 1):
            default_mark = "⭐ " if addr['is_default'] else ""
            text += f"{i}. {default_mark}{addr['label']}\n"
            text += f"   {addr['address']}\n"
    else:
        text += "Адреса не добавлены\n"
    
    text += "\n━━━━━━━━━━━━━━━━"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Имя", callback_data="edit:name")
    kb.button(text="📞 Телефон", callback_data="edit:phone")
    kb.button(text="🏙️ Город", callback_data="edit:city")
    kb.button(text="📍 Адреса", callback_data="manage_addresses")
    kb.button(text="🏠 Меню", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())




async def show_addresses_after_add(callback: CallbackQuery, user_id: int):
    """Показать адреса после добавления"""
    addresses = await get_user_addresses(user_id)
    
    text = "📍 <b>Мои адреса</b>\n\n"
    
    kb = InlineKeyboardBuilder()
    
    for i, addr in enumerate(addresses, 1):
        default_mark = "⭐ " if addr['is_default'] else ""
        text += f"{default_mark}{addr['label']}\n"
        text += f"{addr['address']}\n\n"
        
        kb.button(text=f"❌ Удалить", callback_data=f"delete_addr:{addr['id']}")
        if not addr['is_default']:
            kb.button(text=f"⭐ Основной", callback_data=f"default_addr:{addr['id']}")
    
    kb.adjust(2)
    kb.button(text="➕ Добавить адрес", callback_data="add_address")
    kb.button(text="🔙 Назад", callback_data="profile")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())





@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    """Показать контакты"""
    await callback.message.edit_text(
        "📞 <b>Контакты</b>\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "📍 <b>Адрес:</b>\n"
        "   г. Смоленск, ул. Примерная, 1\n\n"
        "📞 <b>Телефон:</b>\n"
        "   +7 (999) 123-45-67\n\n"
        "🕐 <b>Режим работы:</b>\n"
        "   Ежедневно с 9:00 до 21:00\n\n"
        "🚚 <b>Доставка:</b>\n"
        "   По Смоленску — бесплатно от 2000 ₽",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder()
            .button(text="◀️ Главное меню", callback_data="main_menu")
            .as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    """Показать информацию"""
    await callback.message.edit_text(
        "ℹ️ <b>О магазине Шеф Порт</b>\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🌊 <b>Шеф Порт</b> — ваш проводник в мир свежих морепродуктов!\n\n"
        "🐟 <b>Что мы предлагаем:</b>\n"
        "• Свежая рыба премиум-качества\n"
        "• Замороженные морепродукты\n"
        "• Копчено-соленые деликатесы\n"
        "• Икра и рыбные консервы\n\n"
        "✅ <b>Преимущества:</b>\n"
        "• Доставка в день заказа\n"
        "• Гарантия свежести\n"
        "• Прямые поставки от производителей\n\n"
        "📱 Оформляйте заказы через бота 24/7!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder()
            .button(text="🛍️ Каталог", callback_data="catalog")
            .button(text="◀️ Главное меню", callback_data="main_menu")
            .adjust(1)
            .as_markup()
    )
    await callback.answer()
