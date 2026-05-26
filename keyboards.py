from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from menu_data import MENU, PAYMENT_METHODS


def main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Меню", callback_data="open_menu")
    kb.button(text="🛒 Корзина", callback_data="view_cart")
    kb.button(text="👤 Мой профиль", callback_data="my_profile")
    kb.adjust(2)
    return kb.as_markup()


def categories_keyboard():
    kb = InlineKeyboardBuilder()
    for category in MENU.keys():
        cb_data = f"cat_{category[:30]}"
        kb.button(text=category, callback_data=cb_data)
    kb.button(text="🛒 Корзина", callback_data="view_cart")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def subcategories_keyboard(category: str):
    kb = InlineKeyboardBuilder()
    cat_data = MENU.get(category, {})
    if cat_data.get("_has_subcategories"):
        for subcat in cat_data["subcategories"].keys():
            cb_data = f"sub_{category[:15]}_{subcat[:15]}"
            kb.button(text=subcat, callback_data=cb_data)
    kb.button(text="◀️ Назад", callback_data="open_menu")
    kb.button(text="🛒 Корзина", callback_data="view_cart")
    kb.adjust(2, 1)
    return kb.as_markup()


def items_keyboard(category: str, subcategory: str = None):
    kb = InlineKeyboardBuilder()
    cat_data = MENU.get(category, {})
    
    if subcategory and cat_data.get("_has_subcategories"):
        items = cat_data["subcategories"].get(subcategory, [])
        back_cb = f"cat_{category[:30]}"
    else:
        items = cat_data.get("items", [])
        back_cb = "open_menu"
    
    for i, item in enumerate(items):
        cb_data = f"item_{i}_{category[:10]}_{subcategory[:10] if subcategory else 'none'}"
        kb.button(text=f"{item['name']} — {item['price']}₴", callback_data=cb_data)
    
    kb.button(text="◀️ Назад", callback_data=back_cb)
    kb.button(text="🛒 Корзина", callback_data="view_cart")
    kb.adjust(1)
    return kb.as_markup()


def quantity_keyboard(item_name: str, category: str, subcategory: str = None):
    kb = InlineKeyboardBuilder()
    for qty in [1, 2, 3, 4, 5]:
        cb = f"qty_{qty}_{category[:10]}_{subcategory[:10] if subcategory else 'none'}_{item_name[:20]}"
        kb.button(text=str(qty), callback_data=cb)
    
    back_cb = f"cat_{category[:30]}" if not subcategory else f"sub_{category[:15]}_{subcategory[:15]}"
    kb.button(text="◀️ Назад", callback_data=back_cb)
    kb.adjust(5, 1)
    return kb.as_markup()


def payment_keyboard():
    kb = InlineKeyboardBuilder()
    for i, method in enumerate(PAYMENT_METHODS):
        kb.button(text=method, callback_data=f"pay_{i}")
    kb.button(text="◀️ Назад к корзине", callback_data="view_cart")
    kb.adjust(1)
    return kb.as_markup()


def cart_keyboard(cart_empty: bool = False):
    kb = InlineKeyboardBuilder()
    if not cart_empty:
        kb.button(text="✅ Оформить заказ", callback_data="checkout")
        kb.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    kb.button(text="➕ Добавить ещё", callback_data="open_menu")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def confirm_order_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    kb.button(text="📞 Изменить телефон", callback_data="edit_phone")
    kb.button(text="📍 Изменить адрес", callback_data="edit_address")
    kb.button(text="🗺 Отправить геолокацию", callback_data="send_location")
    kb.button(text="❌ Отменить заказ", callback_data="cancel_order")
    kb.adjust(1)
    return kb.as_markup()


def location_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📍 Отправить геолокацию", request_location=True)
    kb.button(text="◀️ Отмена")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard():
    return ReplyKeyboardRemove()


def group_order_keyboard(order_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принять заказ", callback_data=f"accept_{order_id}")
    kb.button(text="❌ Отклонить заказ", callback_data=f"decline_{order_id}")
    kb.adjust(2)
    return kb.as_markup()


def profile_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить имя", callback_data="edit_name")
    kb.button(text="📞 Изменить телефон", callback_data="edit_phone_profile")
    kb.button(text="📍 Изменить адрес", callback_data="edit_address_profile")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()
