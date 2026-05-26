"""
Простое хранилище данных в памяти.
Для продакшна замените на реальную БД (SQLite, PostgreSQL и т.д.)
"""

from typing import Dict, List, Optional
import time

# Хранилище пользователей: {user_id: {name, phone, address}}
users_db: Dict[int, dict] = {}

# Корзины пользователей: {user_id: [{name, price, qty, category, subcategory}]}
carts: Dict[int, List[dict]] = {}

# Счётчик заказов
order_counter = 0

# История заказов: {order_id: {user_id, items, total, payment, address, phone, status, timestamp}}
orders_db: Dict[int, dict] = {}


def is_registered(user_id: int) -> bool:
    return user_id in users_db


def get_user(user_id: int) -> Optional[dict]:
    return users_db.get(user_id)


def register_user(user_id: int, name: str, phone: str, address: str):
    users_db[user_id] = {
        "name": name,
        "phone": phone,
        "address": address,
    }


def update_user_phone(user_id: int, phone: str):
    if user_id in users_db:
        users_db[user_id]["phone"] = phone


def update_user_address(user_id: int, address: str):
    if user_id in users_db:
        users_db[user_id]["address"] = address


def update_user_name(user_id: int, name: str):
    if user_id in users_db:
        users_db[user_id]["name"] = name


# ---- Корзина ----

def get_cart(user_id: int) -> List[dict]:
    return carts.get(user_id, [])


def add_to_cart(user_id: int, item: dict):
    if user_id not in carts:
        carts[user_id] = []
    # Если такое блюдо уже есть — увеличить количество
    for existing in carts[user_id]:
        if existing["name"] == item["name"]:
            existing["qty"] += item["qty"]
            return
    carts[user_id].append(item.copy())


def clear_cart(user_id: int):
    carts[user_id] = []


def get_cart_total(user_id: int) -> int:
    cart = get_cart(user_id)
    return sum(i["price"] * i["qty"] for i in cart)


def get_cart_text(user_id: int) -> str:
    cart = get_cart(user_id)
    if not cart:
        return "🛒 Корзина пуста"
    
    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    for item in cart:
        subtotal = item["price"] * item["qty"]
        lines.append(f"• {item['name']} × {item['qty']} = <b>{subtotal}₴</b>")
    
    total = get_cart_total(user_id)
    lines.append(f"\n💰 <b>Итого: {total}₴</b>")
    return "\n".join(lines)


# ---- Заказы ----

def create_order(user_id: int, payment_method: str) -> int:
    global order_counter
    order_counter += 1
    order_id = order_counter
    
    user = get_user(user_id)
    cart = get_cart(user_id)
    total = get_cart_total(user_id)
    
    orders_db[order_id] = {
        "order_id": order_id,
        "user_id": user_id,
        "user_name": user["name"],
        "phone": user["phone"],
        "address": user["address"],
        "items": cart.copy(),
        "total": total,
        "payment": payment_method,
        "status": "pending",
        "timestamp": time.strftime("%d.%m.%Y %H:%M"),
    }
    return order_id


def get_order(order_id: int) -> Optional[dict]:
    return orders_db.get(order_id)


def update_order_status(order_id: int, status: str):
    if order_id in orders_db:
        orders_db[order_id]["status"] = status


def format_order_for_group(order_id: int) -> str:
    """Форматирование заказа для отправки в группу"""
    order = get_order(order_id)
    if not order:
        return "Заказ не найден"
    
    lines = [
        f"🆕 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>",
        f"🕐 {order['timestamp']}",
        "",
        f"👤 <b>Клиент:</b> {order['user_name']}",
        f"📞 <b>Телефон:</b> {order['phone']}",
        f"📍 <b>Адрес:</b> {order['address']}",
        "",
        "🍽 <b>Состав заказа:</b>",
    ]
    
    for item in order["items"]:
        subtotal = item["price"] * item["qty"]
        lines.append(f"  • {item['name']} × {item['qty']} шт. = {subtotal}₴")
    
    lines.extend([
        "",
        f"💰 <b>Итого: {order['total']}₴</b>",
        f"💳 <b>Оплата:</b> {order['payment']}",
    ])
    
    return "\n".join(lines)
