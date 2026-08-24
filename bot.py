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

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "0")
)

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

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# DATABASE
# =========================================================

async def db():
    return await aiosqlite.connect(DB_NAME)


# =========================================================
# ADMIN TEKSHIRISH
# =========================================================

def is_admin(user_id: int) -> bool:
    return int(user_id) == ADMIN_ID


# =========================================================
# DATABASE MIGRATION
# =========================================================

async def migrate_database():
    dbx = await db()

    # =====================================================
    # ASOSIY JADVALLAR
    # =====================================================

    await dbx.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    """)

    await dbx.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance INTEGER NOT NULL DEFAULT 10000,
            eggs INTEGER NOT NULL DEFAULT 0,
            storage_capacity INTEGER NOT NULL DEFAULT 1000,
            last_mining INTEGER NOT NULL DEFAULT 0,
            has_deposited INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)

    await dbx.execute("""
        CREATE TABLE IF NOT EXISTS chickens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, level)
        )
    """)

    await dbx.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            proof TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            method TEXT DEFAULT 'card',
            tx_hash TEXT DEFAULT ''
        )
    """)

    await dbx.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            card TEXT DEFAULT '',
            name TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            method TEXT DEFAULT 'card',
            wallet TEXT DEFAULT ''
        )
    """)

    # =====================================================
    # SETTINGS DEFAULT
    # =====================================================

    defaults = {
        "ethereum_wallet": "",
        "card_number": "",
        "chicken_price_1": "1000",
        "chicken_price_2": "5000",
        "chicken_price_3": "15000",
        "egg_exchange_rate": "10",
        "mining_bonus": "100",
        "mining_cooldown": "3600",
    }

    for key, value in defaults.items():
        await dbx.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES(?, ?)
            """,
            (key, value)
        )

    # =====================================================
    # ESKI DATABASE UCHUN MIGRATION
    # =====================================================

    async def add_column_if_missing(table, column, definition):
        cursor = await dbx.execute(
            f"PRAGMA table_info({table})"
        )

        columns = await cursor.fetchall()

        column_names = {
            row[1]
            for row in columns
        }

        if column not in column_names:
            try:
                await dbx.execute(
                    f"""
                    ALTER TABLE {table}
                    ADD COLUMN {column} {definition}
                    """
                )
            except Exception as e:
                logging.warning(
                    "Column qo‘shishda xato %s.%s: %s",
                    table,
                    column,
                    e
                )

    await add_column_if_missing(
        "withdrawals",
        "method",
        "TEXT DEFAULT 'card'"
    )

    await add_column_if_missing(
        "withdrawals",
        "wallet",
        "TEXT DEFAULT ''"
    )

    await add_column_if_missing(
        "deposits",
        "method",
        "TEXT DEFAULT 'card'"
    )

    await add_column_if_missing(
        "deposits",
        "tx_hash",
        "TEXT DEFAULT ''"
    )

    # =====================================================
    # INDEXLAR
    # =====================================================

    await dbx.execute("""
        CREATE INDEX IF NOT EXISTS idx_chickens_user
        ON chickens(user_id)
    """)

    await dbx.execute("""
        CREATE INDEX IF NOT EXISTS idx_deposits_user
        ON deposits(user_id)
    """)

    await dbx.execute("""
        CREATE INDEX IF NOT EXISTS idx_deposits_status
        ON deposits(status)
    """)

    await dbx.execute("""
        CREATE INDEX IF NOT EXISTS idx_withdrawals_user
        ON withdrawals(user_id)
    """)

    await dbx.execute("""
        CREATE INDEX IF NOT EXISTS idx_withdrawals_status
        ON withdrawals(status)
    """)

    await dbx.commit()
    await dbx.close()

    logging.info(
        "✅ Database yaratildi va migration muvaffaqiyatli tugadi."
    )


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
                    text="⛏️ Mining",
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
# FSM STATES
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
# START
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

    rows = [
        [
            InlineKeyboardButton(
                text="🐔 Ferma",
                web_app=WebAppInfo(
                    url=MINI_APP_URL
                )
            )
        ]
    ]

    if is_admin(user.id):
        rows.append(
            [
                InlineKeyboardButton(
                    text="👑 Admin panel",
                    callback_data="admin_home"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=rows
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
# ADMIN COMMAND
# =========================================================

@dp.message(Command("admin"))
async def admin_command(message: Message):

    if not is_admin(message.from_user.id):

        await message.answer(
            "❌ Siz admin emassiz."
        )

        return

    await message.answer(
        "👑 <b>CHICKEN FARM ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# ADMIN HOME
# =========================================================

@dp.callback_query(F.data == "admin_home")
async def admin_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()

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
async def admin_balance(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💰 <b>Balans boshqarish</b>\n\n"
        "Format:\n"
        "<code>ID AMOUNT</code>\n\n"
        "Qo‘shish:\n"
        "<code>123456789 5000</code>\n\n"
        "Ayirish:\n"
        "<code>123456789 -2000</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()

    await state.set_state(AdminStates.balance)


@dp.message(AdminStates.balance)
async def balance_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    try:

        user_id, amount = map(
            int,
            message.text.split()
        )

        dbx = await db()

        cursor = await dbx.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id=?
            """,
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
            (
                new_balance,
                user_id
            )
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ <b>Balans yangilandi</b>\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"💰 Yangi balans: "
            f"<b>{new_balance:,}</b> coin",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Format noto‘g‘ri.\n"
            "Misol: <code>123456789 5000</code>",
            parse_mode="HTML"
        )


# =========================================================
# TOVUQ
# =========================================================

@dp.callback_query(F.data == "admin_chicken")
async def admin_chicken(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🐔 <b>Tovuq boshqarish</b>\n\n"
        "Format:\n"
        "<code>ID LEVEL AMOUNT</code>\n\n"
        "Qo‘shish:\n"
        "<code>123456789 1 5</code>\n\n"
        "Olib tashlash:\n"
        "<code>123456789 1 -2</code>\n\n"
        "LEVEL: 1, 2 yoki 3",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()

    await state.set_state(AdminStates.chicken)


@dp.message(AdminStates.chicken)
async def chicken_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    try:

        user_id, level, amount = map(
            int,
            message.text.split()
        )

        if level not in [1, 2, 3]:
            raise ValueError

        dbx = await db()

        cursor = await dbx.execute(
            """
            SELECT count
            FROM chickens
            WHERE user_id=? AND level=?
            """,
            (
                user_id,
                level
            )
        )

        row = await cursor.fetchone()

        current = int(
            row[0]
        ) if row else 0

        new_count = max(
            0,
            current + amount
        )

        await dbx.execute(
            """
            INSERT INTO chickens
            (user_id, level, count)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, level)
            DO UPDATE SET count=excluded.count
            """,
            (
                user_id,
                level,
                new_count
            )
        )

        await dbx.commit()
        await dbx.close()

        await message.answer(
            f"✅ <b>Tovuq yangilandi!</b>\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"🐔 Lv.{level}: "
            f"<b>{new_count} ta</b>",
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
async def admin_prices(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    values = {}

    for level in [1, 2, 3]:

        cursor = await dbx.execute(
            """
            SELECT value
            FROM settings
            WHERE key=?
            """,
            (f"chicken_price_{level}",)
        )

        row = await cursor.fetchone()

        values[level] = (
            int(row[0])
            if row
            else {
                1: 1000,
                2: 5000,
                3: 15000
            }[level]
        )

    await dbx.close()

    await callback.message.edit_text(
        "💵 <b>Tovuq narxlari</b>\n\n"
        f"🐔 Lv.1: <b>{values[1]:,}</b> coin\n"
        f"🐔 Lv.2: <b>{values[2]:,}</b> coin\n"
        f"🐔 Lv.3: <b>{values[3]:,}</b> coin\n\n"
        "O‘zgartirish uchun:\n"
        "<code>LEVEL PRICE</code>\n\n"
        "Misol:\n"
        "<code>1 2500</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

    await state.set_state(AdminStates.price)


@dp.message(AdminStates.price)
async def price_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    try:

        level, price = map(
            int,
            message.text.split()
        )

        if level not in [1, 2, 3]:
            raise ValueError

        if price <= 0:
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
            "❌ Format noto‘g‘ri.\n"
            "Misol: <code>1 2500</code>",
            parse_mode="HTML"
        )


# =========================================================
# TUXUM KURSI
# =========================================================

@dp.callback_query(F.data == "admin_egg_rate")
async def admin_egg_rate(
    callback: CallbackQuery, state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT value
        FROM settings
        WHERE key='egg_exchange_rate'
        """
    )

    row = await cursor.fetchone()

    rate = int(
        row[0]
    ) if row else 10

    await dbx.close()

    await callback.message.edit_text(
        "🥚 <b>Tuxum → Coin kursi</b>\n\n"
        f"Hozirgi kurs: "
        f"<b>{rate} tuxum = 1 coin</b>\n\n"
        "Yangi kursni yuboring:",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

    await state.set_state(AdminStates.egg_rate)


@dp.message(AdminStates.egg_rate)
async def egg_rate_state(
    message: Message,
    state: FSMContext
):

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
            "❌ Faqat musbat son kiriting."
        )


# =========================================================
# MINING
# =========================================================

@dp.callback_query(F.data == "admin_mining")
async def admin_mining(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

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
                    text="⏱️ Vaqt",
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
async def mining_bonus(
    callback: CallbackQuery, state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💰 Mining bonusini yuboring.\n\n"
        "Masalan:\n"
        "<code>100</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

    await state.set_state(AdminStates.mining_bonus)


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
            f"✅ Mining bonusi: "
            f"<b>{bonus} coin</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        await state.clear()

    except Exception:

        await message.answer(
            "❌ Faqat musbat son kiriting."
        )


@dp.callback_query(F.data == "mining_time")
async def mining_time(
    callback: CallbackQuery, state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "⏱️ Mining vaqtini sekundda yuboring.\n\n"
        "30 daqiqa = <code>1800</code>\n"
        "1 soat = <code>3600</code>\n"
        "2 soat = <code>7200</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

    await state.set_state(AdminStates.mining_time)


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
# TO‘LOV REKVIZITLARI
# =========================================================

@dp.callback_query(F.data == "admin_payment")
async def admin_payment(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT value
        FROM settings
        WHERE key='card_number'
        """
    )

    card_row = await cursor.fetchone()

    cursor = await dbx.execute(
        """
        SELECT value
        FROM settings
        WHERE key='ethereum_wallet'
        """
    )

    eth_row = await cursor.fetchone()

    await dbx.close()

    card = (
        card_row[0]
        if card_row
        else "Belgilanmagan"
    )

    eth = (
        eth_row[0]
        if eth_row and eth_row[0]
        else "Belgilanmagan"
    )

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
        "💳 <b>TO‘LOV REKVIZITLARI</b>\n\n"
        f"💳 Karta:\n"
        f"<code>{card}</code>\n\n"
        f"🔷 Ethereum:\n"
        f"<code>{eth}</code>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# KARTA
# =========================================================

@dp.callback_query(F.data == "set_card")
async def set_card(
    callback: CallbackQuery, state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "💳 Yangi karta raqamini yuboring:",
        reply_markup=back_keyboard()
    )

    await callback.answer()

    await state.set_state(AdminStates.card)


@dp.message(AdminStates.card)
async def card_state(
    message: Message,
    state: FSMContext
):

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


# =========================================================
# ETHEREUM
# =========================================================

@dp.callback_query(F.data == "set_eth")
async def set_eth(
    callback: CallbackQuery, state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔷 Ethereum wallet manzilini yuboring.\n\n"
        "Masalan:\n"
        "<code>0x1234567890123456789012345678901234567890</code>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

    await state.set_state(AdminStates.ethereum)


@dp.message(AdminStates.ethereum)
async def ethereum_state(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    wallet = message.text.strip()

    if (
        not wallet.startswith("0x")
        or len(wallet) != 42
    ):

        await message.answer(
            "❌ Ethereum wallet manzili noto‘g‘ri.\n\n"
            "Wallet 0x bilan boshlanishi va "
            "42 belgidan iborat bo‘lishi kerak."
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
        "✅ <b>Ethereum wallet saqlandi!</b>\n\n"
        f"<code>{wallet}</code>",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )

    await state.clear()


# =========================================================
# DEPOZITLAR
# =========================================================

@dp.callback_query(F.data == "admin_deposits")
async def admin_deposits(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT
            id,
            user_id,
            amount,
            proof,
            created_at
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

    text = (
        "📥 <b>PENDING DEPOZITLAR</b>\n\n"
    )

    buttons = []

    for (
        deposit_id,
        user_id,
        amount,
        proof,
        created_at
    ) in rows:

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

@dp.callback_query(
    F.data.startswith("dep_ok:")
)
async def deposit_approve(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    deposit_id = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT
            user_id,
            amount
        FROM deposits
        WHERE id=? AND status='pending'
        """,
        (deposit_id,)
    )

    row = await cursor.fetchone()

    if not row:

        await dbx.close()

        await callback.answer(
            "❌ Depozit topilmadi yoki allaqachon ishlangan.",
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
        (
            amount,
            user_id
        )
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

    try:

        await bot.send_message(
            user_id,
            "✅ <b>Depozitingiz tasdiqlandi!</b>\n\n"
            f"💰 Balansingizga "
            f"<b>+{amount:,} coin</b> qo‘shildi.\n\n"
            "⛏️ Mining ham ochildi.",
            parse_mode="HTML"
        )

    except Exception as e:

        logging.warning(
            "Userga depozit xabari yuborilmadi: %s",
            e
        )

    await callback.message.edit_text(
        f"✅ <b>Depozit tasdiqlandi</b>\n\n"
        f"🆔 #{deposit_id}\n"
        f"👤 {user_id}\n"
        f"💰 +{amount:,} coin",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )

    await callback.answer(
        "Tasdiqlandi!"
    )


# =========================================================
# DEPOZIT RAD ETISH
# =========================================================

@dp.callback_query(
    F.data.startswith("dep_no:")
)
async def deposit_reject(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    deposit_id = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT user_id
        FROM deposits
        WHERE id=? AND status='pending'
        """,
        (deposit_id,)
    )

    row = await cursor.fetchone()

    if not row:

        await dbx.close()

        await callback.answer(
            "Depozit topilmadi.",
            show_alert=True
        )

        return

    user_id = row[0]

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

    try:

        await bot.send_message(
            user_id,
            "❌ <b>Depozitingiz rad etildi.</b>\n\n"
            "Proof yoki to‘lov ma’lumotlarini tekshiring.",
            parse_mode="HTML"
        )

    except Exception:
        pass

    await callback.message.edit_text(
        f"❌ Depozit #{deposit_id} rad etildi.",
        reply_markup=back_keyboard()
    )

    await callback.answer(
        "Rad etildi."
    )


# =========================================================
# WITHDRAWLAR
# =========================================================

@dp.callback_query(
    F.data == "admin_withdraws"
)
async def admin_withdraws(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    # method va wallet bo‘lgan yangi DB
    try:

        cursor = await dbx.execute(
            """
            SELECT
                id,
                user_id,
                amount,
                card,
                name,
                method,
                wallet,
                created_at
            FROM withdrawals
            WHERE status='pending'
            ORDER BY id DESC
            LIMIT 20
            """
        )

        rows = await cursor.fetchall()

        new_format = True

    except Exception:

        cursor = await dbx.execute(
            """
            SELECT
                id,
                user_id,
                amount,
                card,
                name,
                created_at
            FROM withdrawals
            WHERE status='pending'
            ORDER BY id DESC
            LIMIT 20
            """
        )

        rows = await cursor.fetchall()

        new_format = False

    await dbx.close()

    if not rows:

        await callback.message.edit_text(
            "📤 Hozircha pending withdraw yo‘q.",
            reply_markup=back_keyboard()
        )

        await callback.answer()

        return

    text = (
        "📤 <b>PENDING WITHDRAWLAR</b>\n\n"
    )

    buttons = []

    for row in rows:

        if new_format:

            (
                wid,
                user_id,
                amount,
                card,
                name,
                method,
                wallet,
                created_at
            ) = row

            method = method or "card"
            wallet = wallet or ""

        else:

            (
                wid,
                user_id,
                amount,
                card,
                name,
                created_at
            ) = row

            method = (
                "ethereum"
                if str(card).startswith("0x")
                else "card"
            )

            wallet = (
                card
                if method == "ethereum"
                else ""
            )

        if method.lower() in [
            "eth",
            "ethereum"
        ]:

            payment_info = (
                f"🔷 ETH Wallet:\n"
                f"<code>{wallet or card}</code>\n"
            )

        else:

            payment_info = (
                f"💳 Karta:\n"
                f"<code>{card}</code>\n"
            )

        text += (
            f"🆔 #{wid}\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"💰 {amount:,} coin\n"
            f"{payment_info}"
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

@dp.callback_query(
    F.data.startswith("with_ok:")
)
async def withdraw_approve(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    wid = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT
            user_id,
            amount
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

    try:

        await bot.send_message(
            user_id,
            "✅ <b>Withdraw so‘rovingiz tasdiqlandi!</b>\n\n"
            f"💰 Miqdor: <b>{amount:,} coin</b>\n\n"
            "To‘lov admin tomonidan yuboriladi.",
            parse_mode="HTML"
        )

    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ <b>Withdraw #{wid} tasdiqlandi.</b>\n\n"
        f"💰 {amount:,} coin\n\n"
        "💸 To‘lovni foydalanuvchi ko‘rsatgan "
        "rekvizitga yuboring.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer(
        "Tasdiqlandi!"
    )


# =========================================================
# WITHDRAW RAD ETISH
# =========================================================

@dp.callback_query(
    F.data.startswith("with_no:")
)
async def withdraw_reject(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    wid = int(
        callback.data.split(":")[1]
    )

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT
            user_id,
            amount
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

    # Pulni qaytarish
    await dbx.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
        """,
        (
            amount,
            user_id
        )
    )

    await dbx.execute(
        """
        UPDATE withdrawals
        SET status='rejected'
        WHERE id=? AND status='pending'
        """,
        (wid,)
    )

    await dbx.commit()
    await dbx.close()

    try:

        await bot.send_message(
            user_id,
            "❌ <b>Withdraw so‘rovingiz rad etildi.</b>\n\n"
            f"💰 {amount:,} coin balansingizga qaytarildi.",
            parse_mode="HTML"
        )

    except Exception:
        pass

    await callback.message.edit_text(
        f"❌ <b>Withdraw #{wid} rad etildi.</b>\n\n"
        f"💰 {amount:,} coin balansga qaytarildi.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer(
        "Rad etildi."
    )


# =========================================================
# FOYDALANUVCHILAR
# =========================================================

@dp.callback_query(
    F.data == "admin_users"
)
async def admin_users(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        """
        SELECT
            user_id,
            username,
            first_name,
            balance
        FROM users
        ORDER BY created_at DESC
        LIMIT 20
        """
    )

    rows = await cursor.fetchall()

    await dbx.close()

    text = (
        "👥 <b>OXIRGI FOYDALANUVCHILAR</b>\n\n"
    )

    if not rows:

        text += "Foydalanuvchilar yo‘q."

    for (
        user_id,
        username,
        first_name,
        balance
    ) in rows:

        name = (
            first_name
            or username
            or "Noma'lum"
        )

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

@dp.callback_query(
    F.data == "admin_stats"
)
async def admin_stats(
    callback: CallbackQuery, state: FSMContext
):
    await state.clear()

    if not is_admin(callback.from_user.id):
        return

    dbx = await db()

    cursor = await dbx.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = (
        await cursor.fetchone()
    )[0]

    cursor = await dbx.execute(
        """
        SELECT COALESCE(
            SUM(balance),
            0
        )
        FROM users
        """
    )

    balance = (
        await cursor.fetchone()
    )[0]

    cursor = await dbx.execute(
        """
        SELECT COALESCE(
            SUM(eggs),
            0
        )
        FROM users
        """
    )

    eggs = (
        await cursor.fetchone()
    )[0]

    cursor = await dbx.execute(
        """
        SELECT COALESCE(
            SUM(count),
            0
        )
        FROM chickens
        """
    )

    chickens = (
        await cursor.fetchone()
    )[0]

    cursor = await dbx.execute(
        """
        SELECT COUNT(*)
        FROM deposits
        WHERE status='pending'
        """
    )

    deposits = (
        await cursor.fetchone()
    )[0]

    cursor = await dbx.execute(
        """
        SELECT COUNT(*)
        FROM withdrawals
        WHERE status='pending'
        """
    )

    withdrawals = (
        await cursor.fetchone()
    )[0]

    await dbx.close()

    await callback.message.edit_text(
        "📊 <b>CHICKEN FARM STATISTIKA</b>\n\n"
        f"👥 Foydalanuvchilar: "
        f"<b>{users}</b>\n"
        f"💰 Umumiy coin: "
        f"<b>{balance:,}</b>\n"
        f"🥚 Umumiy tuxum: "
        f"<b>{eggs:,}</b>\n"
        f"🐔 Umumiy tovuq: "
        f"<b>{chickens:,}</b>\n"
        f"📥 Pending depozit: "
        f"<b>{deposits}</b>\n"
        f"📤 Pending withdraw: "
        f"<b>{withdrawals}</b>",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# UNKNOWN CALLBACK
# =========================================================

@dp.callback_query()
async def unknown_callback(
    callback: CallbackQuery
):

    if (
        callback.data
        and callback.data.startswith("admin_")
        and not is_admin(
            callback.from_user.id
        )
    ):

        await callback.answer(
            "❌ Sizda admin huquqi yo‘q.",
            show_alert=True
        )

        return

    await callback.answer()


# =========================================================
# STARTUP
# =========================================================

async def main():

    logging.info(
        "🐔 Chicken Farm bot ishga tushmoqda..."
    )

    # Database migration
    await migrate_database()

    # Eski webhookni o‘chirish
    await bot.delete_webhook(
        drop_pending_updates=True
    )

    logging.info(
        "✅ Bot pollingni boshladi."
    )

    await dp.start_polling(bot)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logging.info(
            "🛑 Bot to‘xtatildi."
        )
