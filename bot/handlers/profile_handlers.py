import logging
import re

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import ProfileStates
from bot.db_postgres import get_user_profile, upsert_user_profile, update_marketing_consent

logger = logging.getLogger(__name__)
router = Router()

FROM_CHECKOUT_FLAG = "from_checkout"

# ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ПОКАЗА ПРОФИЛЯ =====

async def _render_profile(callback_or_message, profile, from_checkout: bool = False):
    address = (
        f"{profile['city']}, {profile['street']}"
        if profile.get("street")
        else profile["city"]
    )
    delivery_text = "🚚 Доставка" if profile["delivery_type"] == "delivery" else "🏃 Самовывоз"
    consent_text = "✅ Да" if profile.get("consent_marketing", 0) else "❌ Нет"

    text = "👤 <b>Ваш профиль</b>\n\n"
    text += f"<b>Имя:</b> {profile['full_name'] or '—'}\n"
    text += f"<b>Телефон:</b> {profile['phone'] or '—'}\n"
    text += f"<b>Адрес:</b> {address or '—'}\n"
    text += f"<b>Способ получения:</b> {delivery_text}\n"
    text += f"<b>Рассылка акций:</b> {consent_text}\n\n"
    text += "Что хотите изменить?"

    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Имя", callback_data="profile:edit:full_name")
    kb.button(text="📞 Телефон", callback_data="profile:edit:phone")
    kb.button(text="📍 Адрес", callback_data="profile:edit:address_single")
    kb.button(text="🚚 / 🏃 Способ получения", callback_data="profile:toggle:delivery")
    kb.button(text="🔔 / 🔕 Рассылка", callback_data="profile:toggle:marketing")

    if from_checkout:
        kb.button(text="⬅️ Назад к оформлению", callback_data="cart:checkout")
    else:
        kb.button(text="◀️ Назад", callback_data="cat:list")

    kb.adjust(2, 2, 1, 1)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=kb.as_markup())
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(text, reply_markup=kb.as_markup())


# ===== ПРОСМОТР ПРОФИЛЯ =====

@router.callback_query(F.data == "profile:view")
async def view_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    if not profile:
        await callback.answer("У вас пока нет профиля", show_alert=True)
        return
    await _render_profile(callback, profile, from_checkout=False)


@router.callback_query(F.data == "profile:view_from_checkout")
async def view_profile_from_checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    if not profile:
        await callback.answer("У вас пока нет профиля", show_alert=True)
        return
    await state.update_data({FROM_CHECKOUT_FLAG: True})
    await _render_profile(callback, profile, from_checkout=True)

@router.callback_query(F.data == "profile:edit")
async def start_profile_edit(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование профиля"""
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    
    if not profile:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    # Сохраняем профиль в state для редактирования
    await state.update_data(editing_profile=True, profile=profile)
    
    text = "✏️ <b>Редактирование профиля</b>\n\n"
    text += "Что хотите изменить?"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Имя", callback_data="profile:edit:name")
    kb.button(text="📞 Телефон", callback_data="profile:edit:phone")
    kb.button(text="📍 Адрес", callback_data="profile:edit:address")
    kb.button(text="❌ Отменить", callback_data="profile")
    kb.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("profile:edit:"))
async def edit_profile_field(callback: CallbackQuery, state: FSMContext):
    """Редактировать конкретное поле"""
    field = callback.data.split(":")[-1]
    
    prompts = {
        'name': "📝 Введите новое имя:",
        'phone': "📞 Введите новый телефон:\n+7 (XXX) XXX-XX-XX",
        'address': "📍 Введите новый адрес доставки:\nул. Ленина, д. 10, кв. 5, под. 2, этаж 3"
    }
    
    await state.update_data(editing_field=field)
    await state.set_state(ProfileStates.editing_field)
    
    text = f"✏️ <b>Редактирование</b>\n\n{prompts.get(field, 'Введите новое значение:')}"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="profile")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(ProfileStates.editing_field)
async def save_edited_field(message: Message, state: FSMContext):
    """Сохранить изменённое поле"""
    user_id = message.from_user.id
    data = await state.get_data()
    field = data.get('editing_field')
    new_value = message.text.strip()
    
    # Валидация
    if field == 'name' and len(new_value) < 2:
        await message.answer("❌ Имя слишком короткое!")
        return
    
    if field == 'phone':
        import re
        phone_clean = re.sub(r'[^\d+]', '', new_value)
        if not re.match(r'^(\+7|8)\d{10}$', phone_clean):
            await message.answer("❌ Неверный формат телефона!")
            return
        if phone_clean.startswith('8'):
            phone_clean = '+7' + phone_clean[1:]
        new_value = phone_clean
    
    if field == 'address' and len(new_value) < 10:
        await message.answer("❌ Адрес слишком короткий!")
        return
    
    # Получаем текущий профиль
    profile = await get_user_profile(user_id)
    
    # Маппинг полей
    field_map = {
        'name': 'full_name',
        'phone': 'phone',
        'address': 'street'
    }
    
    # Обновляем нужное поле
    profile[field_map[field]] = new_value
    
    # ✅ ИСПРАВЛЕНО: Создаём правильный словарь для обновления
    profile_data = {
        'full_name': profile['full_name'],
        'phone': profile['phone'],
        'city': profile.get('city', 'Смоленск'),
        'street': profile.get('street', ''),
        'house': profile.get('house', ''),
        'flat': profile.get('flat', ''),
        'entrance': profile.get('entrance', ''),
        'floor': profile.get('floor', ''),
        'delivery_type': profile.get('delivery_type', 'delivery')
    }
    
    await upsert_user_profile(user_id, profile_data)

    
    try:
        await message.delete()
    except Exception:
        pass
    
    text = "✅ <b>Профиль обновлён!</b>\n\n"
    text += f"📝 <b>ФИО:</b> {profile['full_name']}\n"
    text += f"📞 <b>Телефон:</b> {profile['phone']}\n"
    text += f"🏙️ <b>Город:</b> {profile.get('city', 'Смоленск')}\n"
    
    if profile.get('street'):
        text += f"📍 <b>Адрес:</b> {profile['street']}\n"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Редактировать", callback_data="profile:edit")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await state.clear()



# ===== ПЕРЕКЛЮЧАТЕЛИ =====

@router.callback_query(F.data == "profile:toggle:delivery")
async def toggle_delivery(callback: CallbackQuery):
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    if not profile:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    new_type = "pickup" if profile["delivery_type"] == "delivery" else "delivery"

    await upsert_user_profile(
        user_id=user_id,
        full_name=profile["full_name"],
        phone=profile["phone"],
        city=profile["city"],
        street=profile["street"],
        house=profile["house"],
        flat=profile["flat"],
        entrance=profile["entrance"],
        floor=profile["floor"],
        delivery_type=new_type,
    )

    profile = await get_user_profile(user_id)
    await _render_profile(callback, profile, from_checkout=False)


@router.callback_query(F.data == "profile:toggle:marketing")
async def toggle_marketing(callback: CallbackQuery):
    user_id = callback.from_user.id
    profile = await get_user_profile(user_id)
    if not profile:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    new_consent = 0 if profile.get("consent_marketing", 0) else 1
    update_marketing_consent(user_id, bool(new_consent))

    profile = await get_user_profile(user_id)
    await _render_profile(callback, profile, from_checkout=False)

# ===== ОБРАБОТКА ВВОДА =====

@router.message(ProfileStates.editing_field, F.text)
async def process_field_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    from_checkout = data.get("from_checkout", False)

    user_id = message.from_user.id
    profile = await get_user_profile(user_id)
    new_value = message.text.strip()

    if not profile:
        await message.answer("❌ Профиль не найден, начните через «Мои данные».")
        await state.clear()
        return

    # Имя
    if field == "full_name":
        words = new_value.split()
        if len(words) < 2:
            await message.reply("❌ Введите имя и фамилию (минимум 2 слова)")
            return

        await upsert_user_profile(
            user_id=user_id,
            full_name=new_value,
            phone=profile["phone"],
            city=profile["city"],
            street=profile["street"],
            house=profile["house"],
            flat=profile["flat"],
            entrance=profile["entrance"],
            floor=profile["floor"],
            delivery_type=profile["delivery_type"],
        )

        await state.clear()
        await message.answer("✅ Имя обновлено!")
        profile = await get_user_profile(user_id)
        await _render_profile(message, profile, from_checkout=from_checkout)
        return

    # Телефон
    if field == "phone":
        pattern = r'^(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$'
        if not re.match(pattern, new_value):
            await message.reply("❌ Неверный формат телефона. Пример: +7(900)123-45-67")
            return

        await upsert_user_profile(
            user_id=user_id,
            full_name=profile["full_name"],
            phone=new_value,
            city=profile["city"],
            street=profile["street"],
            house=profile["house"],
            flat=profile["flat"],
            entrance=profile["entrance"],
            floor=profile["floor"],
            delivery_type=profile["delivery_type"],
        )

        await state.clear()
        await message.answer("✅ Телефон обновлён!")
        profile = await get_user_profile(user_id)
        await _render_profile(message, profile, from_checkout=from_checkout)
        return

    # Адрес одной строкой
    if field == "address_single":
        # Простой вариант: город оставляем как есть, всю строку кладём в street
        await upsert_user_profile(
            user_id=user_id,
            full_name=profile["full_name"],
            phone=profile["phone"],
            city=profile["city"] or "г. Смоленск",
            street=new_value,
            house=profile["house"],
            flat=profile["flat"],
            entrance=profile["entrance"],
            floor=profile["floor"],
            delivery_type=profile["delivery_type"],
        )

        await state.clear()
        await message.answer("✅ Адрес обновлён!")
        profile = await get_user_profile(user_id)
        await _render_profile(message, profile, from_checkout=from_checkout)
        return

    await message.answer("❌ Неизвестное поле. Попробуйте ещё раз через «Мои данные».")
    await state.clear()
