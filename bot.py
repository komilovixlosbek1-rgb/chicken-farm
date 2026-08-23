```python
import asyncio
import logging
import os
import time
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# =========================================================
# SOZLAMALAR
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

MINI_APP_URL = "https://chicken-farm-630z.onrender.com"

DB_NAME = "chicken_farm.db"


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN Render Environment Variables'da topilmadi!"
    )

if not ADMIN_ID:
    raise RuntimeError(
        "ADMIN_ID Render Environment Variables'da topilmadi!"
    )


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# ADMIN TEKSHIRISH
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================================================
# DATABASE
# =========================================================

async def db():
    return await aiosqlite.connect(DB_NAME)


# =========================================================
# ADMIN KLAVIATURA
# =========================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Balans boshqarish",
                    callback_data="admin_balance"
                ),
                InlineKeyboardButton(
                    text="🐔 Tovuq boshqarish",
                    callback_data="admin_chicken"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💵 Narxlar",
                    callback_data="admin_prices"
                ),
                InlineKeyboardButton(
                    text="🥚 Tuxum kursi",
                    callback_data="admin_egg_rate"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⛏ Mining",
                    callback_data="admin_mining"
                ),
                InlineKeyboardButton(
                    text="💳 Rekvizitlar",
                    callback_data="admin_payment"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📥 Depozitlar",
                    callback_data="admin_deposits"
                ),
                InlineKeyboardButton(
                    text="📤 Withdraw",
                    callback_data="admin_withdraws"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Foydalanuvchilar",
                    callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="admin_stats"
                ),
            ],
        ]
    )


def back_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data="admin_home"
                )
            ]
        ]
    )


# =========================================================
# FSM
# =========================================================

class AdminStates(StatesGroup):

    balance = State()
    chicken = State()
    price = State()
    egg_rate = State()
    mining_bonus = State()
    mining_time = State()
    card = State()
    ethereum = State()


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start_command(message: Message):

    user = message.from_user

    if not user:
        return

    first_name = user.first_name or "Fermer"

    dbx = await db()

    await dbx.execute(
        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            username,
            first_name,
            balance,
            eggs,
            storage_capacity,
            last_mining,
            has_deposited,
            created_at
        )
        VALUES (?, ?, ?, 10000, 0, 1000, 0, 0, ?)
        """,
        (
            user.id,
            user.username or "",
            first_name,
            int(time.time()),
        )
    )

    await dbx.commit()
    await dbx.close()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐔 Ferma",
                    web_app=WebAppInfo(
                        url=MINI_APP_URL
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Admin panel",
                    callback_data="admin_home"
                )
            ] if is_admin(user.id) else []
        ]
    )

    await message.answer(
        f"🐔 <b>Chicken Farm</b>\n\n"
        f"Salom, <b>{first_name}</b>! 👋\n\n"
        f"Ferma o‘yinini boshlash uchun "
        f"<b>🐔 Ferma</b> tugmasini bosing.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@dp.message(Command("admin"))
async def admin_command(message: Message):

    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz.")
        return

    await message.answer(
        "👑 <b>CHICKEN FARM ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_home")
async def admin_home(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer(
            "❌ Ruxsat yo‘q",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "👑 <b>CHICKEN FARM ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# BALANS
# =========================================================

@dp.callback_query(F.data == "admin_balance")
async def admin_balance(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💰 <b>Balans boshqarish</b>\n\n"
        "Format:\n"
        "<code>ID AMOUNT</code>\n\n"
        "Musbat = qo‘shish\n"
        "Manfiy = ayirish\n\n"
        "Misol:\n"
        "<code>123456789 5000</code>\n"
        "<code>123456789 -2000</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()
    await AdminStates.balance.set()


@dp.message(AdminStates.balance)
async def balance_state(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    try:
        user_id, amount = map(
            int,
            message.text.split()
        )

        dbx = await db()

        cursor = await dbx.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        )

        row = await cursor.fetchone()

        if not row:
            await dbx.close()
            await message.answer(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        new_balance = int(row[0]) + amount

        if new_balance < 0:
            new_balance = 0

        await dbx.execute(
            """
            UPDATE users
            SET balance=?
            WHERE user_id=?
            """,
            (new_balance, user_id)
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Balans yangilandi.\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"💰 Yangi balans: <b>{new_balance:,}</b> coin",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Format noto‘g‘ri.\n"
            "Masalan: <code>123456789 5000</code>",
            parse_mode="HTML"
        )


# =========================================================
# TOVUQ
# =========================================================

@dp.callback_query(F.data == "admin_chicken")
async def admin_chicken(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🐔 <b>Tovuq boshqarish</b>\n\n"
        "Format:\n"
        "<code>ID LEVEL AMOUNT</code>\n\n"
        "Qo‘shish uchun musbat:\n"
        "<code>123456789 1 5</code>\n\n"
        "Olib tashlash uchun manfiy:\n"
        "<code>123456789 1 -2</code>\n\n"
        "LEVEL: 1, 2 yoki 3",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()
    await AdminStates.chicken.set()


@dp.message(AdminStates.chicken)
async def chicken_state(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    try:

        user_id, level, amount = map(
            int,
            message.text.split()
        )

        if level not in [1, 2, 3]:
            await message.answer(
                "❌ Level faqat 1, 2 yoki 3."
            )
            return

        dbx = await db()

        cursor = await dbx.execute(
            """
            SELECT count
            FROM chickens
            WHERE user_id=? AND level=?
            """,
            (user_id, level)
        )

        row = await cursor.fetchone()

        current = int(row[0]) if row else 0
        new_count = max(0, current + amount)

        await dbx.execute(
            """
            INSERT INTO chickens
            (user_id, level, count)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, level)
            DO UPDATE SET count=excluded.count
            """,
            (user_id, level, new_count)
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Tovuq yangilandi!\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"🐔 Lv.{level}: <b>{new_count} ta</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Format noto‘g‘ri.\n"
            "Misol: <code>123456789 1 5</code>",
            parse_mode="HTML"
        )


# =========================================================
# NARXLAR
# =========================================================

@dp.callback_query(F.data == "admin_prices")
async def admin_prices(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💵 <b>Tovuq narxini o‘zgartirish</b>\n\n"
        "Format:\n"
        "<code>LEVEL PRICE</code>\n\n"
        "Misol:\n"
        "<code>1 1000</code>\n"
        "<code>2 5000</code>\n"
        "<code>3 15000</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()
    await AdminStates.price.set()


@dp.message(AdminStates.price)
async def price_state(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    try:

        level, price = map(
            int,
            message.text.split()
        )

        if level not in [1, 2, 3] or price <= 0:
            raise ValueError

        dbx = await db()

        await dbx.execute(
            """
            INSERT INTO settings(key,value)
            VALUES(?,?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (
                f"chicken_price_{level}",
                str(price)
            )
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Lv.{level} narxi "
            f"<b>{price:,} coin</b> bo‘ldi.",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Format noto‘g‘ri. Masalan: "
            "<code>1 2500</code>",
            parse_mode="HTML"
        )


# =========================================================
# TUXUM KURSI
# =========================================================

@dp.callback_query(F.data == "admin_egg_rate")
async def admin_egg_rate(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🥚 <b>Tuxum → Coin kursi</b>\n\n"
        "Masalan:\n"
        "<code>10</code>\n\n"
        "Bu 10 ta tuxum = 1 coin degani.",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()
    await AdminStates.egg_rate.set()


@dp.message(AdminStates.egg_rate)
async def egg_rate_state(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    try:

        rate = int(message.text)

        if rate <= 0:
            raise ValueError

        dbx = await db()

        await dbx.execute(
            """
            INSERT INTO settings(key,value)
            VALUES('egg_exchange_rate',?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (str(rate),)
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Kurs yangilandi:\n"
            f"<b>{rate} tuxum = 1 coin</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Faqat son kiriting."
        )


# =========================================================
# MINING
# =========================================================

@dp.callback_query(F.data == "admin_mining")
async def admin_mining(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Bonus",
                    callback_data="mining_bonus"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏱ Vaqt",
                    callback_data="mining_time"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="admin_home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⛏️ <b>Mining sozlamalari</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "mining_bonus")
async def mining_bonus(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💰 Mining bonusini kiriting.\n\n"
        "Masalan: <code>100</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()
    await AdminStates.mining_bonus.set()


@dp.message(AdminStates.mining_bonus)
async def mining_bonus_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    try:

        bonus = int(message.text)

        if bonus <= 0:
            raise ValueError

        dbx = await db()

        await dbx.execute(
            """
            INSERT INTO settings(key,value)
            VALUES('mining_bonus',?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (str(bonus),)
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Mining bonusi: <b>{bonus} coin</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Faqat musbat son kiriting."
        )


@dp.callback_query(F.data == "mining_time")
async def mining_time(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "⏱ Mining vaqtini sekundda kiriting.\n\n"
        "1 soat = <code>3600</code>\n"
        "30 daqiqa = <code>1800</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()
    await AdminStates.mining_time.set()


@dp.message(AdminStates.mining_time)
async def mining_time_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    try:

        seconds = int(message.text)

        if seconds <= 0:
            raise ValueError

        dbx = await db()

        await dbx.execute(
            """
            INSERT INTO settings(key,value)
            VALUES('mining_cooldown',?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (str(seconds),)
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ Mining vaqti: "
            f"<b>{seconds} sekund</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Faqat musbat son kiriting."
        )


# =========================================================
# REKVIZITLAR
# =========================================================

@dp.callback_query(F.data == "admin_payment")
async def admin_payment(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Karta",
                    callback_data="set_card"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔷 Ethereum",
                    callback_data="set_eth"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="admin_home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "💳 <b>To‘lov rekvizitlari</b>\n\n"
        "Depozit uchun foydalanuvchiga "
        "ko‘rsatiladigan rekvizitlarni sozlang.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "set_card")
async def set_card(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💳 Yangi karta raqamini yuboring:",
        reply_markup=back_keyboard()
    )

    await callback.answer()
    await AdminStates.card.set()


@dp.message(AdminStates.card)
async def card_state(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    card = message.text.strip()

    if len(card) < 8:
        await message.answer(
            "❌ Karta raqami juda qisqa."
        )
        return

    dbx = await db()

    await dbx.execute(
        """
        INSERT INTO settings(key,value)
        VALUES('card_number',?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
        """,
        (card,)
    )

    await dbx.commit()
    await dbx.close()

    await message.answer(
        "✅ Karta rekviziti yangilandi.",
        reply_markup=back_keyboard()
    )

    await state.clear()


@dp.callback_query(F.data == "set_eth")
async def set_eth(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔷 Ethereum wallet manzilini yuboring:",
        reply_markup=back_keyboard()
    )

    await callback.answer()
    await AdminStates.ethereum.set()


@dp.message(AdminStates.ethereum)
async def ethereum_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    wallet = message.text.strip()

    if not wallet.startswith("0x") or len(wallet) != 42:
        await message.answer(
            "❌ Ethereum wallet manzili noto‘g‘ri.\n"
            "0x bilan boshlanishi va 42 belgidan iborat bo‘lishi kerak."
        )
        return

    dbx = await db()

    await dbx.execute(
        """
        INSERT INTO settings(key,value)
        VALUES('ethereum_wallet',?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
        """,
        (wallet,)
    )

    await dbx.commit()
    await dbx.close()

    await message.answer(
        "✅ Ethereum wallet saqlandi.",
        reply_markup=back_keyboard()
    )

    await state.clear()


# =========================================================
# DEPOZITLAR
# =========================================================

@dp.callback_query(F.data == "admin_deposits")
async def admin_deposits(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT id, user_id, amount, proof, created_at
        FROM deposits
        WHERE status='pending'
        ORDER BY id DESC
        LIMIT 20
        """
    )

    rows = await cursor.fetchall()

    await dbx.close()

    if not rows:

        await callback.message.edit_text(
            "📥 Hozircha pending depozit yo‘q.",
            reply_markup=back_keyboard()
        )

        await callback.answer()
        return

    buttons = []

    text = "📥 <b>Pending depozitlar</b>\n\n"

    for deposit_id, user_id, amount, proof, created_at in rows:

        text += (
            f"🆔 #{deposit_id}\n"
            f"👤 <code>{user_id}</code>\n"
            f"💰 {amount:,} coin\n"
            f"🧾 {proof or 'Proof yo‘q'}\n\n"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✅ Tasdiqlash #{deposit_id}",
                    callback_data=f"dep_ok:{deposit_id}"
                ),
                InlineKeyboardButton(
                    text=f"❌ Rad etish #{deposit_id}",
                    callback_data=f"dep_no:{deposit_id}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="admin_home"
            )
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# DEPOZIT TASDIQLASH
# =========================================================

@dp.callback_query(F.data.startswith("dep_ok:"))
async def deposit_approve(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    deposit_id = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT user_id, amount
        FROM deposits
        WHERE id=? AND status='pending'
        """,
        (deposit_id,)
    )

    row = await cursor.fetchone()

    if not row:

        await dbx.close()

        await callback.answer(
            "❌ Depozit topilmadi.",
            show_alert=True
        )
        return

    user_id, amount = row

    await dbx.execute(
        """
        UPDATE users
        SET
            balance = balance + ?,
            has_deposited = 1
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    await dbx.execute(
        """
        UPDATE deposits
        SET status='approved'
        WHERE id=?
        """,
        (deposit_id,)
    )

    await dbx.commit()
    await dbx.close()

    await callback.message.edit_text(
        f"✅ <b>Depozit tasdiqlandi</b>\n\n"
        f"🆔 #{deposit_id}\n"
        f"👤 {user_id}\n"
        f"💰 +{amount:,} coin",
        parse_mode="HTML"
    )

    await callback.answer("Tasdiqlandi!")


# =========================================================
# DEPOZIT RAD ETISH
# =========================================================

@dp.callback_query(F.data.startswith("dep_no:"))
async def deposit_reject(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    deposit_id = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    await dbx.execute(
        """
        UPDATE deposits
        SET status='rejected'
        WHERE id=? AND status='pending'
        """,
        (deposit_id,)
    )

    await dbx.commit()
    await dbx.close()

    await callback.answer(
        "❌ Depozit rad etildi."
    )

    await callback.message.edit_text(
        f"❌ Depozit #{deposit_id} rad etildi.",
        reply_markup=back_keyboard()
    )


# =========================================================
# WITHDRAWLAR
# =========================================================

@dp.callback_query(F.data == "admin_withdraws")
async def admin_withdraws(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT id, user_id, amount, card, name, created_at
        FROM withdrawals
        WHERE status='pending'
        ORDER BY id DESC
        LIMIT 20
        """
    )

    rows = await cursor.fetchall()

    await dbx.close()

    if not rows:

        await callback.message.edit_text(
            "📤 Hozircha pending withdraw yo‘q.",
            reply_markup=back_keyboard()
        )

        await callback.answer()
        return

    text = "📤 <b>Pending withdrawlar</b>\n\n"
    buttons = []

    for wid, user_id, amount, card, name, created_at in rows:

        text += (
            f"🆔 #{wid}\n"
            f"👤 <code>{user_id}</code>\n"
            f"💰 {amount:,} coin\n"
            f"💳 {card}\n"
            f"👤 {name}\n\n"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✅ Tasdiqlash #{wid}",
                    callback_data=f"with_ok:{wid}"
                ),
                InlineKeyboardButton(
                    text=f"❌ Rad etish #{wid}",
                    callback_data=f"with_no:{wid}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="admin_home"
            )
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# WITHDRAW TASDIQLASH
# =========================================================

@dp.callback_query(F.data.startswith("with_ok:"))
async def withdraw_approve(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    wid = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    await dbx.execute(
        """
        UPDATE withdrawals
        SET status='approved'
        WHERE id=? AND status='pending'
        """,
        (wid,)
    )

    await dbx.commit()
    await dbx.close()

    await callback.message.edit_text(
        f"✅ Withdraw #{wid} tasdiqlandi.\n\n"
        f"💸 Foydalanuvchiga to‘lovni "
        f"belgilangan rekvizit bo‘yicha yuboring.",
        reply_markup=back_keyboard()
    )

    await callback.answer("Tasdiqlandi!")


# =========================================================
# WITHDRAW RAD ETISH
# =========================================================

@dp.callback_query(F.data.startswith("with_no:"))
async def withdraw_reject(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    wid = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT user_id, amount
        FROM withdrawals
        WHERE id=? AND status='pending'
        """,
        (wid,)
    )

    row = await cursor.fetchone()

    if not row:

        await dbx.close()

        await callback.answer(
            "Withdraw topilmadi.",
            show_alert=True
        )
        return

    user_id, amount = row

    # Pul foydalanuvchiga qaytariladi
    await dbx.execute(
        """
        UPDATE users
        SET balance=balance+?
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    await dbx.execute(
        """
        UPDATE withdrawals
        SET status='rejected'
        WHERE id=?
        """,
        (wid,)
    )

    await dbx.commit()
    await dbx.close()

    await callback.message.edit_text(
        f"❌ Withdraw #{wid} rad etildi.\n\n"
        f"💰 {amount:,} coin foydalanuvchi balansiga qaytarildi.",
        reply_markup=back_keyboard()
    )

    await callback.answer("Rad etildi!")


# =========================================================
# FOYDALANUVCHILAR
# =========================================================

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT user_id, username, first_name, balance
        FROM users
        ORDER BY created_at DESC
        LIMIT 20
        """
    )

    rows = await cursor.fetchall()

    await dbx.close()

    text = "👥 <b>Oxirgi foydalanuvchilar</b>\n\n"

    for user_id, username, first_name, balance in rows:

        name = first_name or username or "Noma'lum"

        text += (
            f"👤 {name}\n"
            f"🆔 <code>{user_id}</code>\n"
            f"💰 {balance:,} coin\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# STATISTIKA
# =========================================================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = (await cursor.fetchone())[0]

    cursor = await dbx.execute(
        "SELECT COALESCE(SUM(balance),0) FROM users"
    )

    balance = (await cursor.fetchone())[0]

    cursor = await dbx.execute(
        "SELECT COALESCE(SUM(eggs),0) FROM users"
    )

    eggs = (await cursor.fetchone())[0]

    cursor = await dbx.execute(
        "SELECT COALESCE(SUM(count),0) FROM chickens"
    )

    chickens = (await cursor.fetchone())[0]

    cursor = await dbx.execute(
        """
        SELECT COUNT(*)
        FROM deposits
        WHERE status='pending'
        """
    )

    deposits = (await cursor.fetchone())[0]

    cursor = await dbx.execute(
        """
        SELECT COUNT(*)
        FROM withdrawals
        WHERE status='pending'
        """
    )

    withdrawals = (await cursor.fetchone())[0]

    await dbx.close()

    await callback.message.edit_text(
        "📊 <b>CHICKEN FARM STATISTIKA</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"💰 Umumiy coin: <b>{balance:,}</b>\n"
        f"🥚 Umumiy tuxum: <b>{eggs:,}</b>\n"
        f"🐔 Umumiy tovuq: <b>{chickens:,}</b>\n"
        f"📥 Pending depozit: <b>{deposits}</b>\n"
        f"📤 Pending withdraw: <b>{withdrawals}</b>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# NOMA'LUM ADMIN CALLBACKLARINI HIMOYA
# =========================================================

@dp.callback_query()
async def unknown_callback(callback: CallbackQuery):

    if callback.data and callback.data.startswith("admin_"):

        if not is_admin(callback.from_user.id):

            await callback.answer(
                "❌ Sizda admin huquqi yo‘q.",
                show_alert=True
            )

            return

    await callback.answer()


# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():

    logging.info(
        "🐔 Chicken Farm bot ishga tushmoqda..."
    )

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        logging.info(
            "Bot to‘xtatildi."
        )
```

