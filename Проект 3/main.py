import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup,
                          InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "hidden"
ADMIN_IDS = ["709307873"]  

logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                          id INTEGER PRIMARY KEY,
                          name TEXT,
                          description TEXT,
                          price INTEGER
                      )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                          id INTEGER PRIMARY KEY,
                          user_id INTEGER,
                          name TEXT,
                          phone TEXT,
                          address TEXT,
                          product TEXT,
                          status TEXT
                      )''')
conn.commit()

class OrderFSM(StatesGroup):
    name = State()
    phone = State()
    address = State()
    product = State()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/catalog")],
        [KeyboardButton(text="/help"), KeyboardButton(text="/info")]
    ],
    resize_keyboard=True
)

@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    logging.info(f"User {message.from_user.id} started bot.")
    await message.answer("Вітаємо в магазині! Оберіть команду з меню:", reply_markup=main_kb)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("/catalog - Переглянути каталог\n"
                         "/admin - Панель адміністратора")

@dp.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer("Це Telegram-бот для оформлення замовлень. Розробник: @kpojiebapka")

@dp.message(Command("catalog"))
async def show_catalog(message: Message):
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    if not products:
        await message.answer("Каталог порожній.")
        return
    for pid, name, desc, price in products:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Замовити", callback_data=f"order_{pid}")]
        ])
        await message.answer(f"<b>{name}</b>\n{desc}\nЦіна: {price} грн", reply_markup=kb)

@dp.callback_query(F.data.startswith("order_"))
async def fsm_start(callback: CallbackQuery, state: FSMContext):
    pid = int(callback.data.split("_")[1])
    cursor.execute("SELECT name FROM products WHERE id = ?", (pid,))
    product = cursor.fetchone()
    if not product:
        await callback.message.answer("Товар не знайдено.")
        return
    await state.update_data(product=product[0])
    await state.set_state(OrderFSM.name)
    await callback.message.answer("Введіть ваше ім'я:")
    await callback.answer()

@dp.message(OrderFSM.name)
async def fsm_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderFSM.phone)
    await message.answer("Введіть ваш номер телефону:")

@dp.message(OrderFSM.phone)
async def fsm_phone(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Телефон має містити лише цифри.")
        return
    await state.update_data(phone=message.text)
    await state.set_state(OrderFSM.address)
    await message.answer("Введіть адресу доставки:")

@dp.message(OrderFSM.address)
async def fsm_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    cursor.execute("INSERT INTO orders (user_id, name, phone, address, product, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, data['name'], data['phone'], data['address'], data['product'], "Очікує обробку"))
    conn.commit()
    await message.answer("Замовлення прийняте! Очікуйте дзвінка менеджера.")
    logging.info(f"Нове замовлення: {data}")
    await state.clear()

@dp.message(Command(commands=["admin"]))
async def admin_panel(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("Доступ заборонено.")
        return
    await message.answer("/add_item — додати товар\n/remove_item — видалити товар\n/orders — перегляд замовлень")

@dp.message(Command(commands=["add_item"]))
async def add_item(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        parts = message.text.split(maxsplit=3)
        name, desc, price = parts[1], parts[2], int(parts[3])
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, desc, price))
        conn.commit()
        await message.answer("Товар додано.")
    except:
        await message.answer("Формат: /add_item Назва Опис Ціна")

@dp.message(Command(commands=["remove_item"]))
async def remove_item(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        pid = int(message.text.split()[1])
        cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
        conn.commit()
        await message.answer("Товар видалено.")
    except:
        await message.answer("Формат: /remove_item ID")

@dp.message(Command(commands=["orders"]))
async def show_orders(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    if not orders:
        await message.answer("Немає замовлень.")
        return
    for order in orders:
        await message.answer(f"ID: {order[0]}\nІм'я: {order[2]}\nТелефон: {order[3]}\nАдреса: {order[4]}\n"
                             f"Товар: {order[5]}\nСтатус: {order[6]}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())