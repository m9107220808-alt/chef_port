from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Состояния для заполнения профиля пользователя"""
    full_name = State()
    phone = State()
    city = State()
    street = State()
    house = State()
    flat = State()
    entrance = State()
    floor = State()
    confirm = State()
    editing_field = State()
    editing_name = State()
    editing_phone = State()
    editing_city = State()
    editing_street = State()
    managing_addresses = State()
    waiting_for_new_address = State()
    waiting_for_address_label = State()


class CheckoutStates(StatesGroup):
    """Состояния для оформления заказа"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_delivery_address = State()
    waiting_for_comment = State()
    waiting_for_payment = State()    
    choosing_delivery_method = State()
    choosing_address = State()    
    confirming_new_address = State()
    confirming_address = State()
    choosing_payment_method = State()
    choosing_change = State()    
    confirming_order = State()


class WeightInputState(StatesGroup):
    """Состояние для ввода веса товара"""
    waiting_for_weight = State()
