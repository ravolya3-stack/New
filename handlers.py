import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import GROUP_ID, CAFE_NAME, CURRENCY
from states import RegistrationStates, OrderStates
from keyboards import (
    main_menu_keyboard, categories_keyboard, subcategories_keyboard,
    items_keyboard, quantity_keyboard, payment_keyboard, cart_keyboard,
    confirm_order_keyboard, location_keyboard, remove_keyboard,
    group_order_keyboard, profile_keyboard
)
from menu_data import MENU, PAYMENT_METHODS
import database as db

router = Router()
logger = logging.getLogger(__name__)


# ===========================
# СТАРТ / РЕГИСТРАЦИЯ
# ===========================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if db.is_registered(user_id):
        user = db.get_user(user_id)
        await message.answer(
            f"👋 С возвращением, <b>{user['name']}</b>!\n\n"
            f"Добро пожаловать в {CAFE_NAME}",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в {CAFE_NAME}!\n\n"
            "Для оформления заказов нужно зарегистрироваться.\n\n"
            "📝 <b>Введите ваше имя:</b>",
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.waiting_name)


@router.message(RegistrationStates.waiting_name)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введите ваше имя:")
        return
    await state.update_data(name=name)
    await message.answer(
        f"✅ Отлично, <b>{name}</b>!\n\n"
        "📞 <b>Введите ваш номер телефона:</b>\n"
        "Например: +380501234567",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.waiting_phone)


@router.message(RegistrationStates.waiting_phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 7:
        await message.answer("⚠️ Некорректный номер. Введите телефон ещё раз:")
        return
    await state.update_data(phone=phone)
    await message.answer(
        "📍 <b>Введите ваш адрес доставки:</b>\n"
        "Например: ул. Центральная, 15, кв. 3",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.waiting_address)


@router.message(RegistrationStates.waiting_address)
async def reg_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("⚠️ Адрес слишком короткий. Введите полный адрес:")
        return
    
    data = await state.get_data()
    db.register_user(message.from_user.id, data["name"], data["phone"], address)
    await state.clear()
    
    await message.answer(
        f"🎉 <b>Регистрация завершена!</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📍 Адрес: {address}\n\n"
        f"Теперь вы можете делать заказы в {CAFE_NAME}!",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


# ===========================
# ГЛАВНОЕ МЕНЮ
# ===========================

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        f"🏠 <b>Главное меню</b>\n\n{CAFE_NAME}",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


# ===========================
# МЕНЮ / КАТЕГОРИИ
# ===========================

@router.callback_query(F.data == "open_menu")
async def cb_open_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.browsing_categories)
    await call.message.edit_text(
        "📋 <b>Выберите категорию:</b>",
        reply_markup=categories_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(call: CallbackQuery, state: FSMContext):
    # Найти категорию по префиксу
    prefix = call.data[4:]  # убрать "cat_"
    category = next((c for c in MENU if c[:30] == prefix), None)
    
    if not category:
        await call.answer("Категория не найдена")
        return
    
    cat_data = MENU[category]
    await state.update_data(current_category=category)
    
    if cat_data.get("_has_subcategories"):
        await state.set_state(OrderStates.browsing_subcategories)
        await call.message.edit_text(
            f"{category}\n\n<b>Выберите подкатегорию:</b>",
            reply_markup=subcategories_keyboard(category),
            parse_mode="HTML"
        )
    else:
        await state.set_state(OrderStates.browsing_items)
        items = cat_data.get("items", [])
        items_text = "\n".join([f"• {i['name']} — {i['price']}{CURRENCY}\n  <i>{i['description']}</i>" for i in items])
        await call.message.edit_text(
            f"{category}\n\n{items_text}\n\n<b>Выберите блюдо:</b>",
            reply_markup=items_keyboard(category),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("sub_"))
async def cb_subcategory(call: CallbackQuery, state: FSMContext):
    parts = call.data[4:].split("_", 1)
    if len(parts) < 2:
        await call.answer("Ошибка")
        return
    
    cat_prefix, sub_prefix = parts[0], parts[1]
    category = next((c for c in MENU if c[:15] == cat_prefix), None)
    if not category:
        await call.answer("Ошибка")
        return
    
    cat_data = MENU[category]
    subcategory = next((s for s in cat_data.get("subcategories", {}) if s[:15] == sub_prefix), None)
    if not subcategory:
        await call.answer("Ошибка")
        return
    
    await state.update_data(current_category=category, current_subcategory=subcategory)
    await state.set_state(OrderStates.browsing_items)
    
    items = cat_data["subcategories"][subcategory]
    items_text = "\n".join([f"• {i['name']} — {i['price']}{CURRENCY}\n  <i>{i['description']}</i>" for i in items])
    
    await call.message.edit_text(
        f"{category} › {subcategory}\n\n{items_text}\n\n<b>Выберите блюдо:</b>",
        reply_markup=items_keyboard(category, subcategory),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("item_"))
async def cb_item(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    # item_{index}_{cat_prefix}_{sub_prefix}
    item_idx = int(parts[1])
    cat_prefix = parts[2]
    sub_prefix = parts[3] if len(parts) > 3 else "none"
    
    category = next((c for c in MENU if c[:10] == cat_prefix), None)
    if not category:
        await call.answer("Ошибка")
        return
    
    cat_data = MENU[category]
    
    if sub_prefix != "none":
        subcategory = next((s for s in cat_data.get("subcategories", {}) if s[:10] == sub_prefix), None)
        items = cat_data["subcategories"].get(subcategory, []) if subcategory else []
    else:
        subcategory = None
        items = cat_data.get("items", [])
    
    if item_idx >= len(items):
        await call.answer("Блюдо не найдено")
        return
    
    item = items[item_idx]
    await state.update_data(
        selected_item=item,
        current_category=category,
        current_subcategory=subcategory
    )
    await state.set_state(OrderStates.choosing_quantity)
    
    await call.message.edit_text(
        f"🍽 <b>{item['name']}</b>\n"
        f"<i>{item['description']}</i>\n"
        f"💰 Цена: <b>{item['price']}{CURRENCY}</b>\n\n"
        f"Выберите количество:",
        reply_markup=quantity_keyboard(item['name'], category, subcategory),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("qty_"))
async def cb_quantity(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    qty = int(parts[1])
    
    data = await state.get_data()
    item = data.get("selected_item")
    
    if not item:
        await call.answer("Ошибка")
        return
    
    cart_item = {
        "name": item["name"],
        "price": item["price"],
        "qty": qty,
    }
    db.add_to_cart(call.from_user.id, cart_item)
    
    subtotal = item["price"] * qty
    total = db.get_cart_total(call.from_user.id)
    
    await call.answer(f"✅ Добавлено: {item['name']} × {qty}", show_alert=False)
    
    await call.message.edit_text(
        f"✅ <b>Добавлено в корзину!</b>\n\n"
        f"• {item['name']} × {qty} = <b>{subtotal}{CURRENCY}</b>\n\n"
        f"💰 Итого в корзине: <b>{total}{CURRENCY}</b>\n\n"
        f"Что дальше?",
        reply_markup=cart_keyboard(),
        parse_mode="HTML"
    )


# ===========================
# КОРЗИНА
# ===========================

@router.callback_query(F.data == "view_cart")
async def cb_view_cart(call: CallbackQuery, state: FSMContext):
    cart = db.get_cart(call.from_user.id)
    cart_text = db.get_cart_text(call.from_user.id)
    
    await call.message.edit_text(
        cart_text,
        reply_markup=cart_keyboard(cart_empty=len(cart) == 0),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(call: CallbackQuery, state: FSMContext):
    db.clear_cart(call.from_user.id)
    await call.answer("🗑 Корзина очищена")
    await call.message.edit_text(
        "🛒 Корзина пуста",
        reply_markup=cart_keyboard(cart_empty=True),
        parse_mode="HTML"
    )


# ===========================
# ОФОРМЛЕНИЕ ЗАКАЗА
# ===========================

@router.callback_query(F.data == "checkout")
async def cb_checkout(call: CallbackQuery, state: FSMContext):
    cart = db.get_cart(call.from_user.id)
    if not cart:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    await state.set_state(OrderStates.choosing_payment)
    await call.message.edit_text(
        f"{db.get_cart_text(call.from_user.id)}\n\n"
        "💳 <b>Выберите способ оплаты:</b>",
        reply_markup=payment_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_"))
async def cb_payment(call: CallbackQuery, state: FSMContext):
    pay_idx = int(call.data[4:])
    payment_method = PAYMENT_METHODS[pay_idx]
    
    await state.update_data(payment_method=payment_method)
    await state.set_state(OrderStates.confirming_order)
    
    user = db.get_user(call.from_user.id)
    cart_text = db.get_cart_text(call.from_user.id)
    
    await call.message.edit_text(
        f"📋 <b>Подтверждение заказа</b>\n\n"
        f"{cart_text}\n\n"
        f"👤 <b>Имя:</b> {user['name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"📍 <b>Адрес:</b> {user['address']}\n"
        f"💳 <b>Оплата:</b> {payment_method}\n\n"
        "Проверьте данные и подтвердите заказ:",
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "edit_phone")
async def cb_edit_phone(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.editing_phone)
    await call.message.edit_text(
        "📞 <b>Введите новый номер телефона:</b>",
        parse_mode="HTML"
    )


@router.message(OrderStates.editing_phone)
async def process_new_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 7:
        await message.answer("⚠️ Некорректный номер. Попробуйте ещё раз:")
        return
    
    db.update_user_phone(message.from_user.id, phone)
    await state.set_state(OrderStates.confirming_order)
    
    data = await state.get_data()
    payment_method = data.get("payment_method", "—")
    user = db.get_user(message.from_user.id)
    cart_text = db.get_cart_text(message.from_user.id)
    
    await message.answer(
        f"✅ Телефон обновлён!\n\n"
        f"📋 <b>Подтверждение заказа</b>\n\n"
        f"{cart_text}\n\n"
        f"👤 <b>Имя:</b> {user['name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"📍 <b>Адрес:</b> {user['address']}\n"
        f"💳 <b>Оплата:</b> {payment_method}",
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "edit_address")
async def cb_edit_address(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.editing_address)
    await call.message.edit_text(
        "📍 <b>Введите новый адрес доставки:</b>",
        parse_mode="HTML"
    )


@router.message(OrderStates.editing_address)
async def process_new_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("⚠️ Адрес слишком короткий. Попробуйте ещё раз:")
        return
    
    db.update_user_address(message.from_user.id, address)
    await state.set_state(OrderStates.confirming_order)
    
    data = await state.get_data()
    payment_method = data.get("payment_method", "—")
    user = db.get_user(message.from_user.id)
    cart_text = db.get_cart_text(message.from_user.id)
    
    await message.answer(
        f"✅ Адрес обновлён!\n\n"
        f"📋 <b>Подтверждение заказа</b>\n\n"
        f"{cart_text}\n\n"
        f"👤 <b>Имя:</b> {user['name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"📍 <b>Адрес:</b> {user['address']}\n"
        f"💳 <b>Оплата:</b> {payment_method}",
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "send_location")
async def cb_send_location(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.waiting_location)
    await call.message.answer(
        "📍 Нажмите кнопку ниже, чтобы отправить вашу геолокацию:",
        reply_markup=location_keyboard()
    )


@router.message(OrderStates.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext, bot: Bot):
    lat = message.location.latitude
    lon = message.location.longitude
    address = f"📍 Геолокация: {lat:.5f}, {lon:.5f}"
    
    db.update_user_address(message.from_user.id, address)
    await state.set_state(OrderStates.confirming_order)
    
    data = await state.get_data()
    payment_method = data.get("payment_method", "—")
    user = db.get_user(message.from_user.id)
    cart_text = db.get_cart_text(message.from_user.id)
    
    await message.answer(
        f"✅ Геолокация сохранена!\n\n"
        f"📋 <b>Подтверждение заказа</b>\n\n"
        f"{cart_text}\n\n"
        f"👤 <b>Имя:</b> {user['name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"📍 <b>Адрес:</b> {user['address']}\n"
        f"💳 <b>Оплата:</b> {payment_method}",
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.message(OrderStates.waiting_location, F.text == "◀️ Отмена")
async def cancel_location(message: Message, state: FSMContext):
    await state.set_state(OrderStates.confirming_order)
    data = await state.get_data()
    payment_method = data.get("payment_method", "—")
    user = db.get_user(message.from_user.id)
    cart_text = db.get_cart_text(message.from_user.id)
    
    await message.answer(
        f"📋 <b>Подтверждение заказа</b>\n\n"
        f"{cart_text}\n\n"
        f"👤 <b>Имя:</b> {user['name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"📍 <b>Адрес:</b> {user['address']}\n"
        f"💳 <b>Оплата:</b> {payment_method}",
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_order")
async def cb_confirm_order(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    payment_method = data.get("payment_method", "Не указан")
    
    order_id = db.create_order(call.from_user.id, payment_method)
    order = db.get_order(order_id)
    
    # Отправить заказ в группу
    order_text = db.format_order_for_group(order_id)
    
    try:
        # Отправляем заказ в группу
        group_msg = await bot.send_message(
            GROUP_ID,
            order_text,
            reply_markup=group_order_keyboard(order_id),
            parse_mode="HTML"
        )
        
        # Если был отправлен location — пересылаем в группу
        if "Геолокация:" in order.get("address", ""):
            await bot.send_message(GROUP_ID, f"📍 Геолокация клиента для заказа #{order_id} указана в координатах выше")
    
    except Exception as e:
        logger.error(f"Не удалось отправить заказ в группу: {e}")
    
    db.clear_cart(call.from_user.id)
    await state.clear()
    
    await call.message.edit_text(
        f"🎉 <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"Мы получили ваш заказ и скоро с вами свяжемся.\n\n"
        f"💰 Сумма: <b>{order['total']}{CURRENCY}</b>\n"
        f"💳 Оплата: {payment_method}\n\n"
        "Спасибо, что выбрали нас! 🙏",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_order")
async def cb_cancel_order(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "❌ <b>Заказ отменён</b>\n\n"
        "Ваша корзина сохранена. Вы можете вернуться к оформлению в любое время.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


# ===========================
# ОБРАБОТКА КНОПОК В ГРУППЕ
# ===========================

@router.callback_query(F.data.startswith("accept_"))
async def cb_accept_order(call: CallbackQuery, bot: Bot):
    order_id = int(call.data[7:])
    order = db.get_order(order_id)
    
    if not order:
        await call.answer("Заказ не найден")
        return
    
    if order["status"] != "pending":
        await call.answer(f"Заказ уже обработан: {order['status']}")
        return
    
    db.update_order_status(order_id, "accepted")
    admin_name = call.from_user.full_name
    
    # Обновить сообщение в группе
    await call.message.edit_text(
        call.message.text + f"\n\n✅ <b>ПРИНЯТ</b> — {admin_name}",
        parse_mode="HTML"
    )
    
    # Уведомить клиента
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ <b>Ваш заказ #{order_id} принят!</b>\n\n"
            f"Мы уже готовим ваш заказ на сумму <b>{order['total']}{CURRENCY}</b>.\n"
            "Скоро привезём! 🚀",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить клиента: {e}")
    
    await call.answer("✅ Заказ принят!")


@router.callback_query(F.data.startswith("decline_"))
async def cb_decline_order(call: CallbackQuery, bot: Bot):
    order_id = int(call.data[8:])
    order = db.get_order(order_id)
    
    if not order:
        await call.answer("Заказ не найден")
        return
    
    if order["status"] != "pending":
        await call.answer(f"Заказ уже обработан: {order['status']}")
        return
    
    db.update_order_status(order_id, "declined")
    admin_name = call.from_user.full_name
    
    await call.message.edit_text(
        call.message.text + f"\n\n❌ <b>ОТКЛОНЁН</b> — {admin_name}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            order["user_id"],
            f"😔 <b>Заказ #{order_id} отклонён</b>\n\n"
            "К сожалению, мы не можем выполнить ваш заказ прямо сейчас.\n"
            "Пожалуйста, свяжитесь с нами или попробуйте позже.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить клиента: {e}")
    
    await call.answer("❌ Заказ отклонён")


# ===========================
# ПРОФИЛЬ
# ===========================

@router.callback_query(F.data == "my_profile")
async def cb_profile(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if not user:
        await call.answer("Профиль не найден")
        return
    
    await call.message.edit_text(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"Имя: <b>{user['name']}</b>\n"
        f"📞 Телефон: <b>{user['phone']}</b>\n"
        f"📍 Адрес: <b>{user['address']}</b>",
        reply_markup=profile_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "edit_name")
async def cb_edit_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationStates.waiting_name)
    await state.update_data(editing_profile=True)
    await call.message.edit_text("✏️ <b>Введите новое имя:</b>", parse_mode="HTML")


@router.callback_query(F.data == "edit_phone_profile")
async def cb_edit_phone_profile(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.editing_phone)
    await state.update_data(editing_profile=True)
    await call.message.edit_text("📞 <b>Введите новый номер телефона:</b>", parse_mode="HTML")


@router.callback_query(F.data == "edit_address_profile")
async def cb_edit_address_profile(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.editing_address)
    await state.update_data(editing_profile=True)
    await call.message.edit_text("📍 <b>Введите новый адрес:</b>", parse_mode="HTML")
