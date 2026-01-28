from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛍️ Каталог товаров")
    builder.button(text="🛒 Моя корзина")
    builder.button(text="📋 Мои заказы")
    builder.button(text="☎️ Контакты")
    builder.button(text="❓ Информация")
    builder.button(text="👤 Мои данные")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ---------- Inline-клавиатуры: категории / товары ----------

def category_keyboard(categories: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in categories.items():
        builder.button(text=name, callback_data=f"cat:{code}")
    builder.adjust(2)
    
    # Мои заказы и Корзина в одном ряду [image:17]
    builder.row(
        InlineKeyboardButton(text="📋 Мои заказы", callback_data="orders:back_menu"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart:view_inline")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main"))
    return builder.as_markup()

def products_keyboard_from_db(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # ✅ ИСПРАВЛЕНО: добавлен category_id (8 полей вместо 7)
    for p_id, category_id, p_code, name, price_per_kg, is_weighted, min_weight_kg, desc in products:
        builder.button(
            text=f"{name} — {price_per_kg} ₽/кг",
            callback_data=f"prod:{p_id}",
        )
    
    builder.button(text="🔙 Назад к категориям", callback_data="cat:list")
    builder.adjust(1)
    return builder.as_markup()


def cart_inline_keyboard(cart_has_items: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура для простого просмотра корзины.
    Если корзина пуста — только кнопка перехода в каталог.
    """
    builder = InlineKeyboardBuilder()

    if cart_has_items:
        builder.button(text="🗑️ Очистить корзину", callback_data="cart:clear")
        builder.button(text="➕ Продолжить покупки", callback_data="cart:continue")
        builder.button(text="✅ Оформить заказ", callback_data="cart:checkout")
        builder.adjust(2)
    else:
        builder.button(text="🛍️ В каталог", callback_data="cat:list")

    return builder.as_markup()


def cart_manage_inline_keyboard(cart: list) -> InlineKeyboardMarkup:
    """
    Подробная клавиатура корзины: удаление конкретных позиций, очистка, оформление, возврат к каталогу.

    :param cart: список элементов корзины вида
                 [{'product_id': 1, 'name': 'Семга', 'qty': 2, ...}, ...]
    """
    builder = InlineKeyboardBuilder()

    # Кнопки удаления каждой позиции
    for item in cart:
        builder.button(
            text=f"❌ {item['name']}",
            callback_data=f"cart:remove:{item['product_id']}",
        )

    # Общие действия
    if cart:
        builder.button(text="🗑️ Очистить всё", callback_data="cart:clear")
        builder.button(text="✅ Оформить заказ", callback_data="cart:checkout")

    builder.button(text="➕ Еще товаров", callback_data="cat:list")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Inline-клавиатуры: количество / вес ----------

def quantity_keyboard(product_code: str) -> InlineKeyboardMarkup:
    """Вход в счетчик для штучного товара (начало с 1 шт)"""
    return item_counter_keyboard(product_code, 1.0, is_weighted=False)

def weighted_quantity_keyboard(product_code: str, min_weight_kg: float) -> InlineKeyboardMarkup:
    """Вход в счетчик для весового товара (начало с мин. веса)"""
    return item_counter_keyboard(product_code, min_weight_kg, is_weighted=True)

def item_counter_keyboard(p_code: str, current_qty: float, is_weighted: bool) -> InlineKeyboardMarkup:
    """Универсальный счетчик для Web App интерфейса"""
    builder = InlineKeyboardBuilder()
    current_qty = round(current_qty, 1)
    
    if is_weighted:
        # Панель управления весом: -0.5, -0.1, [вес], +0.1, +0.5
        builder.row(
            InlineKeyboardButton(text="-0.5", callback_data=f"count:m05:{p_code}:{current_qty}"),
            InlineKeyboardButton(text="-0.1", callback_data=f"count:m01:{p_code}:{current_qty}"),
            InlineKeyboardButton(text=f" {current_qty} кг ", callback_data="count:ignore"),
            InlineKeyboardButton(text="+0.1", callback_data=f"count:p01:{p_code}:{current_qty}"),
            InlineKeyboardButton(text="+0.5", callback_data=f"count:p05:{p_code}:{current_qty}")
        )
    else:
        # Панель для штучного товара: -1, [кол-во], +1
        builder.row(
            InlineKeyboardButton(text=" ➖ ", callback_data=f"count:m10:{p_code}:{current_qty}"),
            InlineKeyboardButton(text=f" {int(current_qty)} шт ", callback_data="count:ignore"),
            InlineKeyboardButton(text=" ➕ ", callback_data=f"count:p10:{p_code}:{current_qty}")
        )
    
    # Кнопка подтверждения и возврата
    builder.row(InlineKeyboardButton(text="📥 Добавить в корзину", callback_data=f"count:confirm:{p_code}:{current_qty}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="cat:list"))
    
    return builder.as_markup()


def cart_manage_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки удаления каждой позиции
    for item in items:
        builder.button(
            text=f"❌ {item['name']}",
            callback_data=f"cart:remove:{item['product_code']}",
        )

    # Общие действия
    builder.button(text="🗑️ Очистить всё", callback_data="cart:clear")
    builder.button(text="✅ Оформить заказ", callback_data="cart:checkout")
    builder.button(text="➕ Еще товаров", callback_data="cat:list")
    builder.adjust(1)
    return builder.as_markup()

def payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💵 Нал, без сдачи", callback_data="pay:cash_no_change")
    builder.button(text="💵 Нал, нужна сдача", callback_data="pay:cash_change")
    builder.button(text="💳 Безнал (перевод)", callback_data="pay:card")
    builder.adjust(1)
    return builder.as_markup()

def item_counter_keyboard(p_code: str, current_qty: float, is_weighted: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_qty = round(current_qty, 1) # Защита от кривых дробей 0.1+0.2
    
    if is_weighted:
        # Ряд для крупных изменений
        builder.row(
            InlineKeyboardButton(text="-0.5", callback_data=f"count:m05:{p_code}:{current_qty}"),
            InlineKeyboardButton(text="-0.1", callback_data=f"count:m01:{p_code}:{current_qty}"),
            InlineKeyboardButton(text=f" {current_qty} кг ", callback_data="count:ignore"),
            InlineKeyboardButton(text="+0.1", callback_data=f"count:p01:{p_code}:{current_qty}"),
            InlineKeyboardButton(text="+0.5", callback_data=f"count:p05:{p_code}:{current_qty}")
        )
    else:
        # Для штучного товара оставляем просто -1 / +1
        builder.row(
            InlineKeyboardButton(text=" ➖ ", callback_data=f"count:m10:{p_code}:{current_qty}"),
            InlineKeyboardButton(text=f" {int(current_qty)} шт ", callback_data="count:ignore"),
            InlineKeyboardButton(text=" ➕ ", callback_data=f"count:p10:{p_code}:{current_qty}")
        )
    
    # Кнопка подтверждения (Premium-стиль)
    builder.row(
        InlineKeyboardButton(text="✨ Добавить в корзину", callback_data=f"count:confirm:{p_code}:{current_qty}")
    )
    
    # Кнопка возврата
    builder.row(InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="cat:list"))
    
    return builder.as_markup()
