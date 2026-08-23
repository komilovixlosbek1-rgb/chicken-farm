import time
import aiosqlite
from typing import Optional

DB_NAME = "chicken_farm.db"


# =========================================================
# DATABASE
# =========================================================

async def get_db():
    return await aiosqlite.connect(DB_NAME)


# =========================================================
# INIT DATABASE
# =========================================================

async def init_db():
    db = await get_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance INTEGER DEFAULT 10000,
            eggs INTEGER DEFAULT 0,
            storage_capacity INTEGER DEFAULT 1000,
            last_mining INTEGER DEFAULT 0,
            has_deposited INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT 0
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS chickens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(user_id, level)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            proof TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT 0
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            card TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT 0
        )
    """)

    default_settings = [
        ("card_number", "8600 **** **** ****"),
        ("egg_exchange_rate", "10"),
        ("mining_bonus", "100"),
        ("mining_cooldown", "3600"),
    ]

    for key, value in default_settings:
        await db.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))

    await db.commit()
    await db.close()


# =========================================================
# USER
# =========================================================

async def get_user(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT
            user_id,
            username,
            first_name,
            balance,
            eggs,
            storage_capacity,
            last_mining,
            has_deposited,
            created_at
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    await cursor.close()
    await db.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "balance": int(row[3]),
        "eggs": int(row[4]),
        "storage_capacity": int(row[5]),
        "last_mining": int(row[6]),
        "has_deposited": int(row[7]),
        "created_at": int(row[8]),
    }


async def create_user(
    user_id: int,
    username: str = "",
    first_name: str = ""
):
    db = await get_db()

    await db.execute("""
        INSERT OR IGNORE INTO users (
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
    """, (
        user_id,
        username,
        first_name,
        int(time.time())
    ))

    await db.commit()
    await db.close()


# =========================================================
# SETTINGS
# =========================================================

async def get_setting(key: str):
    db = await get_db()

    cursor = await db.execute("""
        SELECT value
        FROM settings
        WHERE key = ?
    """, (key,))

    row = await cursor.fetchone()

    await cursor.close()
    await db.close()

    if not row:
        return None

    return row[0]


async def get_settings():
    """
    Barcha sozlamalarni bitta dict ko'rinishida qaytaradi.
    api.py aynan shu funksiyadan foydalanadi.
    """

    db = await get_db()

    cursor = await db.execute("""
        SELECT key, value
        FROM settings
    """)

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    values = {
        key: value
        for key, value in rows
    }

    return {
        "card_number": values.get(
            "card_number",
            "8600 **** **** ****"
        ),
        "egg_exchange_rate": int(
            values.get("egg_exchange_rate", 10)
        ),
        "mining_bonus": int(
            values.get("mining_bonus", 100)
        ),
        "mining_cooldown": int(
            values.get("mining_cooldown", 3600)
        ),
    }


async def set_setting(key: str, value: str):
    db = await get_db()

    await db.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, str(value)))

    await db.commit()
    await db.close()


# =========================================================
# CHICKENS
# =========================================================

async def get_chickens(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT level, count
        FROM chickens
        WHERE user_id = ?
        ORDER BY level ASC
    """, (user_id,))

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return [
        {
            "level": int(level),
            "count": int(count)
        }
        for level, count in rows
    ]


# =========================================================
# BUY CHICKEN
# =========================================================

async def buy_chicken(
    user_id: int,
    level: int
):
    prices = {
        1: 1000,
        2: 5000,
        3: 15000
    }

    if level not in prices:
        return {
            "success": False,
            "message": "Tovuq darajasi noto'g'ri"
        }

    price = prices[level]

    db = await get_db()

    cursor = await db.execute("""
        SELECT balance
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    if not row:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Foydalanuvchi topilmadi"
        }

    balance = int(row[0])

    if balance < price:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Balansingiz yetarli emas"
        }

    await db.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE user_id = ?
    """, (price, user_id))

    await db.execute("""
        INSERT INTO chickens
            (user_id, level, count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, level)
        DO UPDATE SET count = count + 1
    """, (user_id, level))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"Lv.{level} tovuq sotib olindi!",
        "level": level,
        "price": price
    }


# =========================================================
# EGGS
# =========================================================

async def get_egg_storage(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT eggs
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    await cursor.close()
    await db.close()

    if not row:
        return 0

    return int(row[0])


async def generate_eggs(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT level, count
        FROM chickens
        WHERE user_id = ?
    """, (user_id,))

    chickens = await cursor.fetchall()

    if not chickens:
        await cursor.close()
        await db.close()
        return 0

    rates = {
        1: 1,
        2: 3,
        3: 8
    }

    total_per_call = 0

    for level, count in chickens:
        total_per_call += rates.get(
            int(level), 0
        ) * int(count)

    cursor2 = await db.execute("""
        SELECT eggs, storage_capacity
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user_row = await cursor2.fetchone()

    if not user_row:
        await cursor.close()
        await cursor2.close()
        await db.close()
        return 0

    current_eggs = int(user_row[0])
    capacity = int(user_row[1])

    new_total = min(
        capacity,
        current_eggs + total_per_call
    )

    await db.execute("""
        UPDATE users
        SET eggs = ?
        WHERE user_id = ?
    """, (new_total, user_id))

    await db.commit()

    await cursor.close()
    await cursor2.close()
    await db.close()

    return new_total


# =========================================================
# EXCHANGE EGGS
# =========================================================

async def exchange_eggs(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT eggs
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    if not row:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Foydalanuvchi topilmadi"
        }

    eggs = int(row[0])

    cursor2 = await db.execute("""
        SELECT value
        FROM settings
        WHERE key = 'egg_exchange_rate'
    """)

    rate_row = await cursor2.fetchone()

    rate = int(rate_row[0]) if rate_row else 10

    if eggs < rate:
        await cursor.close()
        await cursor2.close()
        await db.close()

        return {
            "success": False,
            "message": f"Kamida {rate} ta tuxum kerak"
        }

    coins = eggs // rate
    remaining_eggs = eggs % rate

    await db.execute("""
        UPDATE users
        SET
            eggs = ?,
            balance = balance + ?
        WHERE user_id = ?
    """, (
        remaining_eggs,
        coins,
        user_id
    ))

    await db.commit()

    await cursor.close()
    await cursor2.close()
    await db.close()

    return {
        "success": True,
        "message": f"{eggs} ta tuxum {coins} coin ga almashtirildi!",
        "eggs_used": eggs - remaining_eggs,
        "coins": coins,
        "remaining_eggs": remaining_eggs
    }


# =========================================================
# MINING
# =========================================================

async def claim_mining(user_id: int):
    db = await get_db()

    cursor = await db.execute("""
        SELECT
            balance,
            last_mining,
            has_deposited
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    if not row:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Foydalanuvchi topilmadi"
        }

    balance = int(row[0])
    last_mining = int(row[1])
    has_deposited = int(row[2])

    if not has_deposited:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Mining uchun avval depozit qiling"
        }

    now = int(time.time())

    cooldown = int(
        await get_setting("mining_cooldown") or 3600
    )

    bonus = int(
        await get_setting("mining_bonus") or 100
    )

    if now - last_mining < cooldown:
        remaining = cooldown - (
            now - last_mining
        )

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": f"Bonus hali tayyor emas. {remaining} soniya kuting",
            "remaining": remaining
        }

    await db.execute("""
        UPDATE users
        SET
            balance = balance + ?,
            last_mining = ?
        WHERE user_id = ?
    """, (
        bonus,
        now,
        user_id
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"+{bonus} coin olindi!",
        "bonus": bonus,
        "balance": balance + bonus
    }


# =========================================================
# DEPOSIT
# =========================================================

async def create_deposit(
    user_id: int,
    amount: int,
    proof: str = ""
):
    if amount < 5000:
        return {
            "success": False,
            "message": "Minimal depozit 5 000 coin"
        }

    db = await get_db()

    await db.execute("""
        INSERT INTO deposits (
            user_id,
            amount,
            proof,
            status,
            created_at
        )
        VALUES (?, ?, ?, 'pending', ?)
    """, (
        user_id,
        amount,
        proof,
        int(time.time())
    ))

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": "Depozit so‘rovi yuborildi!",
        "amount": amount,
        "status": "pending"
    }


# =========================================================
# WITHDRAW
# =========================================================

async def create_withdraw(
    user_id: int,
    amount: int,
    card: str,
    name: str
):
    if amount < 10000:
        return {
            "success": False,
            "message": "Minimal chiqarish 10 000 coin"
        }

    db = await get_db()

    cursor = await db.execute("""
        SELECT balance
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = await cursor.fetchone()

    if not row:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Foydalanuvchi topilmadi"
        }

    balance = int(row[0])

    if balance < amount:
        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Balansingiz yetarli emas"
        }

    await db.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE user_id = ?
    """, (amount, user_id))

    await db.execute("""
        INSERT INTO withdrawals (
            user_id,
            amount,
            card,
            name,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (
        user_id,
        amount,
        card,
        name,
        int(time.time())
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Pul chiqarish so‘rovi yuborildi!",
        "amount": amount,
        "status": "pending"
    }
