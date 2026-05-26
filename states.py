from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()


class OrderStates(StatesGroup):
    browsing_categories = State()
    browsing_subcategories = State()
    browsing_items = State()
    choosing_quantity = State()
    choosing_payment = State()
    viewing_cart = State()
    confirming_order = State()
    editing_phone = State()
    editing_address = State()
    waiting_location = State()
