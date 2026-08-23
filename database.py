import time
import aiosqlite
from typing import Optional

DB_NAME = "chicken_farm.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

async def get_db():
    return await aiosqlite.connect(DB_NAME)


# =========================================================
# INIT DATABASE
# =========================================================

async def init_db():
    db = await get_db()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CHICKENS
    # -----------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS chickens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(user_id, level)
        )
    """)

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    """)

    # -----------------------------------------------------
    # DEPOSITS
    # -----------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            method TEXT DEFAULT 'card',
            proof TEXT DEFAULT '',
            tx_hash TEXT DEFAULT '',
            wallet TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            admin_note TEXT DEFAULT '',
            created_at INTEGER DEFAULT 0,
            processed_at INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # WITHDRAWALS
    # -----------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            method TEXT DEFAULT 'card',
            card TEXT DEFAULT '',
            wallet TEXT DEFAULT '',
            name TEXT DEFAULT '',
            tx_hash TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            admin_note TEXT DEFAULT '',
            created_at INTEGER DEFAULT 0,
            processed_at INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # TRANSACTIONS
    # -----------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # DEFAULT SETTINGS
    # -----------------------------------------------------

    default_settings = [

        # Admin
        ("admin_id", ""),

        # Chicken prices
        ("chicken_price_1", "1000"),
        ("chicken_price_2", "5000"),
        ("chicken_price_3", "15000"),

        # Chicken production
        ("chicken_rate_1", "1"),
        ("chicken_rate_2", "3"),
        ("chicken_rate_3", "8"),

        # Eggs
        ("egg_exchange_rate", "10"),

        # Mining
        ("mining_bonus", "100"),
        ("mining_cooldown", "3600"),

        # Storage
        ("egg_capacity", "1000"),

        # Card payment
        ("card_number", "8600 **** **** ****"),

        # Crypto
        ("eth_deposit_wallet", ""),
        ("eth_withdraw_wallet", ""),

        # Crypto exchange
        ("eth_coin_rate", "100000"),

        # Minimum deposits
        ("deposit_min", "5000"),
        ("withdraw_min", "10000"),
        ("eth_deposit_min", "1"),
        ("eth_withdraw_min", "10000"),
    ]

    for key, value in default_settings:

        await db.execute("""
            INSERT OR IGNORE INTO settings
            (key, value)
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
# ALL USERS
# =========================================================

async def get_all_users():

    db = await get_db()

    cursor = await db.execute("""
        SELECT
            user_id,
            username,
            first_name,
            balance,
            eggs,
            has_deposited,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "balance": int(row[3]),
            "eggs": int(row[4]),
            "has_deposited": int(row[5]),
            "created_at": int(row[6]),
        }
        for row in rows
    ]


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


async def set_setting(
    key: str,
    value
):

    db = await get_db()

    await db.execute("""
        INSERT INTO settings (
            key,
            value
        )
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (
        key,
        str(value)
    ))

    await db.commit()
    await db.close()


async def get_settings():

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
        "admin_id": values.get(
            "admin_id",
            ""
        ),

        "card_number": values.get(
            "card_number",
            ""
        ),

        "eth_deposit_wallet": values.get(
            "eth_deposit_wallet",
            ""
        ),

        "eth_withdraw_wallet": values.get(
            "eth_withdraw_wallet",
            ""
        ),

        "eth_coin_rate": int(
            values.get(
                "eth_coin_rate",
                100000
            )
        ),

        "chicken_price_1": int(
            values.get(
                "chicken_price_1",
                1000
            )
        ),

        "chicken_price_2": int(
            values.get(
                "chicken_price_2",
                5000
            )
        ),

        "chicken_price_3": int(
            values.get(
                "chicken_price_3",
                15000
            )
        ),

        "chicken_rate_1": int(
            values.get(
                "chicken_rate_1",
                1
            )
        ),

        "chicken_rate_2": int(
            values.get(
                "chicken_rate_2",
                3
            )
        ),

        "chicken_rate_3": int(
            values.get(
                "chicken_rate_3",
                8
            )
        ),

        "egg_exchange_rate": int(
            values.get(
                "egg_exchange_rate",
                10
            )
        ),

        "mining_bonus": int(
            values.get(
                "mining_bonus",
                100
            )
        ),

        "mining_cooldown": int(
            values.get(
                "mining_cooldown",
                3600
            )
        ),

        "egg_capacity": int(
            values.get(
                "egg_capacity",
                1000
            )
        ),

        "deposit_min": int(
            values.get(
                "deposit_min",
                5000
            )
        ),

        "withdraw_min": int(
            values.get(
                "withdraw_min",
                10000
            )
        ),

        "eth_deposit_min": int(
            values.get(
                "eth_deposit_min",
                1
            )
        ),

        "eth_withdraw_min": int(
            values.get(
                "eth_withdraw_min",
                10000
            )
        ),
    }


# =========================================================
# BALANCE
# =========================================================

async def add_balance(
    user_id: int,
    amount: int,
    description: str = "Admin balans qo‘shdi"
):

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

    await db.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'admin_add', ?, ?, ?)
    """, (
        user_id,
        amount,
        description,
        int(time.time())
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "balance": int(row[0]) + amount
    }


async def remove_balance(
    user_id: int,
    amount: int,
    description: str = "Admin balans ayirdi"
):

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
            "message": "Foydalanuvchi balansi yetarli emas"
        }

    await db.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'admin_remove', ?, ?, ?)
    """, (
        user_id,
        amount,
        description,
        int(time.time())
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "balance": balance - amount
    }


# =========================================================
# CHICKENS
# =========================================================

async def get_chickens(
    user_id: int
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT
            level,
            count
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


async def get_chicken_price(
    level: int
):

    return int(
        await get_setting(
            f"chicken_price_{level}"
        ) or {
            1: 1000,
            2: 5000,
            3: 15000
        }.get(level, 0)
    )


async def buy_chicken(
    user_id: int,
    level: int
):

    if level not in [1, 2, 3]:

        return {
            "success": False,
            "message": "Tovuq darajasi noto‘g‘ri"
        }

    price = await get_chicken_price(level)

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
    """, (
        price,
        user_id
    ))

    await db.execute("""
        INSERT INTO chickens (
            user_id,
            level,
            count
        )
        VALUES (?, ?, 1)

        ON CONFLICT(user_id, level)
        DO UPDATE SET
            count = count + 1
    """, (
        user_id,
        level
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'chicken_buy', ?, ?, ?)
    """, (
        user_id,
        price,
        f"Lv.{level} tovuq sotib olindi",
        int(time.time())
    ))

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
# ADMIN CHICKEN GIVE / REMOVE
# =========================================================

async def admin_add_chicken(
    user_id: int,
    level: int,
    count: int
):

    if level not in [1, 2, 3]:

        return {
            "success": False,
            "message": "Daraja noto‘g‘ri"
        }

    if count <= 0:

        return {
            "success": False,
            "message": "Miqdor noto‘g‘ri"
        }

    db = await get_db()

    await db.execute("""
        INSERT INTO chickens (
            user_id,
            level,
            count
        )
        VALUES (?, ?, ?)

        ON CONFLICT(user_id, level)
        DO UPDATE SET
            count = count + excluded.count
    """, (
        user_id,
        level,
        count
    ))

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": f"{count} ta Lv.{level} tovuq berildi"
    }


async def admin_remove_chicken(
    user_id: int,
    level: int,
    count: int
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT count
        FROM chickens
        WHERE user_id = ?
        AND level = ?
    """, (
        user_id,
        level
    ))

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Bunday tovuq yo‘q"
        }

    current = int(row[0])

    if current < count:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Tovuq soni yetarli emas"
        }

    new_count = current - count

    if new_count == 0:

        await db.execute("""
            DELETE FROM chickens
            WHERE user_id = ?
            AND level = ?
        """, (
            user_id,
            level
        ))

    else:

        await db.execute("""
            UPDATE chickens
            SET count = ?
            WHERE user_id = ?
            AND level = ?
        """, (
            new_count,
            user_id,
            level
        ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"{count} ta Lv.{level} tovuq olib tashlandi"
    }


# =========================================================
# EGGS
# =========================================================

async def get_egg_storage(
    user_id: int
):

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


async def generate_eggs(
    user_id: int
):

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
        1: int(
            await get_setting("chicken_rate_1") or 1
        ),
        2: int(
            await get_setting("chicken_rate_2") or 3
        ),
        3: int(
            await get_setting("chicken_rate_3") or 8
        )
    }

    total = 0

    for level, count in chickens:

        total += (
            rates.get(
                int(level),
                0
            ) *
            int(count)
        )

    cursor2 = await db.execute("""
        SELECT
            eggs,
            storage_capacity
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
        current_eggs + total
    )

    await db.execute("""
        UPDATE users
        SET eggs = ?
        WHERE user_id = ?
    """, (
        new_total,
        user_id
    ))

    await db.commit()

    await cursor.close()
    await cursor2.close()
    await db.close()

    return new_total


# =========================================================
# EXCHANGE EGGS
# =========================================================

async def exchange_eggs(
    user_id: int
):

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

    rate = int(
        await get_setting(
            "egg_exchange_rate"
        ) or 10
    )

    if eggs < rate:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": f"Kamida {rate} ta tuxum kerak"
        }

    coins = eggs // rate
    remaining = eggs % rate

    await db.execute("""
        UPDATE users
        SET
            eggs = ?,
            balance = balance + ?
        WHERE user_id = ?
    """, (
        remaining,
        coins,
        user_id
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'egg_exchange', ?, ?, ?)
    """, (
        user_id,
        coins,
        f"{eggs} tuxum almashtirildi",
        int(time.time())
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"{eggs} ta tuxum {coins} coin ga almashtirildi!",
        "coins": coins,
        "remaining_eggs": remaining
    }


# =========================================================
# MINING
# =========================================================

async def claim_mining(
    user_id: int
):

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

    cooldown = int(
        await get_setting(
            "mining_cooldown"
        ) or 3600
    )

    bonus = int(
        await get_setting(
            "mining_bonus"
        ) or 100
    )

    now = int(time.time())

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

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'mining', ?, ?, ?)
    """, (
        user_id,
        bonus,
        "Mining bonus",
        now
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
    proof: str = "",
    method: str = "card",
    tx_hash: str = "",
    wallet: str = ""
):

    minimum = int(
        await get_setting(
            "deposit_min"
        ) or 5000
    )

    if amount < minimum:

        return {
            "success": False,
            "message": f"Minimal depozit {minimum} coin"
        }

    db = await get_db()

    await db.execute("""
        INSERT INTO deposits (
            user_id,
            amount,
            method,
            proof,
            tx_hash,
            wallet,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        user_id,
        amount,
        method,
        proof,
        tx_hash,
        wallet,
        int(time.time())
    ))

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": "Depozit so‘rovi yuborildi!",
        "amount": amount,
        "method": method,
        "status": "pending"
    }


# =========================================================
# GET DEPOSITS
# =========================================================

async def get_deposits(
    status: Optional[str] = None
):

    db = await get_db()

    if status:

        cursor = await db.execute("""
            SELECT
                id,
                user_id,
                amount,
                method,
                proof,
                tx_hash,
                wallet,
                status,
                admin_note,
                created_at,
                processed_at
            FROM deposits
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))

    else:

        cursor = await db.execute("""
            SELECT
                id,
                user_id,
                amount,
                method,
                proof,
                tx_hash,
                wallet,
                status,
                admin_note,
                created_at,
                processed_at
            FROM deposits
            ORDER BY created_at DESC
        """)

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "amount": row[2],
            "method": row[3],
            "proof": row[4],
            "tx_hash": row[5],
            "wallet": row[6],
            "status": row[7],
            "admin_note": row[8],
            "created_at": row[9],
            "processed_at": row[10]
        }
        for row in rows
    ]


# =========================================================
# APPROVE DEPOSIT
# =========================================================

async def approve_deposit(
    deposit_id: int,
    admin_note: str = ""
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT
            user_id,
            amount,
            status
        FROM deposits
        WHERE id = ?
    """, (deposit_id,))

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Deposit topilmadi"
        }

    user_id = int(row[0])
    amount = int(row[1])
    status = row[2]

    if status != "pending":

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Bu deposit allaqachon ko‘rib chiqilgan"
        }

    now = int(time.time())

    await db.execute("""
        UPDATE deposits
        SET
            status = 'approved',
            admin_note = ?,
            processed_at = ?
        WHERE id = ?
    """, (
        admin_note,
        now,
        deposit_id
    ))

    await db.execute("""
        UPDATE users
        SET
            balance = balance + ?,
            has_deposited = 1
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'deposit', ?, ?, ?)
    """, (
        user_id,
        amount,
        f"Deposit #{deposit_id} tasdiqlandi",
        now
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Deposit tasdiqlandi"
    }


# =========================================================
# REJECT DEPOSIT
# =========================================================

async def reject_deposit(
    deposit_id: int,
    admin_note: str = ""
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT status
        FROM deposits
        WHERE id = ?
    """, (deposit_id,))

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Deposit topilmadi"
        }

    if row[0] != "pending":

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Deposit allaqachon ko‘rib chiqilgan"
        }

    await db.execute("""
        UPDATE deposits
        SET
            status = 'rejected',
            admin_note = ?,
            processed_at = ?
        WHERE id = ?
    """, (
        admin_note,
        int(time.time()),
        deposit_id
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Deposit rad etildi"
    }


# =========================================================
# WITHDRAW
# =========================================================

async def create_withdraw(
    user_id: int,
    amount: int,
    card: str = "",
    name: str = "",
    method: str = "card",
    wallet: str = ""
):

    minimum = int(
        await get_setting(
            "withdraw_min"
        ) or 10000
    )

    if amount < minimum:

        return {
            "success": False,
            "message": f"Minimal chiqarish {minimum} coin"
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
    """, (
        amount,
        user_id
    ))

    await db.execute("""
        INSERT INTO withdrawals (
            user_id,
            amount,
            method,
            card,
            wallet,
            name,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        user_id,
        amount,
        method,
        card,
        wallet,
        name,
        int(time.time())
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'withdraw_request', ?, ?, ?)
    """, (
        user_id,
        amount,
        "Withdraw so‘rovi",
        int(time.time())
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Pul chiqarish so‘rovi yuborildi!",
        "amount": amount,
        "method": method,
        "status": "pending"
    }


# =========================================================
# GET WITHDRAWALS
# =========================================================

async def get_withdrawals(
    status: Optional[str] = None
):

    db = await get_db()

    if status:

        cursor = await db.execute("""
            SELECT
                id,
                user_id,
                amount,
                method,
                card,
                wallet,
                name,
                tx_hash,
                status,
                admin_note,
                created_at,
                processed_at
            FROM withdrawals
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))

    else:

        cursor = await db.execute("""
            SELECT
                id,
                user_id,
                amount,
                method,
                card,
                wallet,
                name,
                tx_hash,
                status,
                admin_note,
                created_at,
                processed_at
            FROM withdrawals
            ORDER BY created_at DESC
        """)

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "amount": row[2],
            "method": row[3],
            "card": row[4],
            "wallet": row[5],
            "name": row[6],
            "tx_hash": row[7],
            "status": row[8],
            "admin_note": row[9],
            "created_at": row[10],
            "processed_at": row[11]
        }
        for row in rows
    ]


# =========================================================
# APPROVE WITHDRAW
# =========================================================

async def approve_withdraw(
    withdraw_id: int,
    tx_hash: str = "",
    admin_note: str = ""
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT
            user_id,
            amount,
            status
        FROM withdrawals
        WHERE id = ?
    """, (withdraw_id,))

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Withdraw topilmadi"
        }

    user_id = int(row[0])
    amount = int(row[1])
    status = row[2]

    if status != "pending":

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Bu withdraw allaqachon ko‘rib chiqilgan"
        }

    now = int(time.time())

    await db.execute("""
        UPDATE withdrawals
        SET
            status = 'approved',
            tx_hash = ?,
            admin_note = ?,
            processed_at = ?
        WHERE id = ?
    """, (
        tx_hash,
        admin_note,
        now,
        withdraw_id
    ))

    await db.execute("""
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, 'withdraw', ?, ?, ?)
    """, (
        user_id,
        amount,
        f"Withdraw #{withdraw_id} tasdiqlandi",
        now
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Withdraw tasdiqlandi"
    }


# =========================================================
# REJECT WITHDRAW
# =========================================================

async def reject_withdraw(
    withdraw_id: int,
    admin_note: str = ""
):

    db = await get_db()

    cursor = await db.execute("""
        SELECT
            user_id,
            amount,
            status
        FROM withdrawals
        WHERE id = ?
    """, (withdraw_id,))

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Withdraw topilmadi"
        }

    user_id = int(row[0])
    amount = int(row[1])
    status = row[2]

    if status != "pending":

        await cursor.close()
        await db.close()

        return {
            "success": False,
            "message": "Withdraw allaqachon ko‘rib chiqilgan"
        }

    # Reject bo‘lsa pulni foydalanuvchiga qaytaramiz
    await db.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    await db.execute("""
        UPDATE withdrawals
        SET
            status = 'rejected',
            admin_note = ?,
            processed_at = ?
        WHERE id = ?
    """, (
        admin_note,
        int(time.time()),
        withdraw_id
    ))

    await db.commit()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Withdraw rad etildi va coin qaytarildi"
    }


# =========================================================
# STATISTICS
# =========================================================

async def get_statistics():

    db = await get_db()

    cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total_users = int(
        (await cursor.fetchone())[0]
    )

    cursor = await db.execute("""
        SELECT COALESCE(SUM(balance), 0)
        FROM users
    """)

    total_balance = int(
        (await cursor.fetchone())[0]
    )

    cursor = await db.execute("""
        SELECT COALESCE(SUM(eggs), 0)
        FROM users
    """)

    total_eggs = int(
        (await cursor.fetchone())[0]
    )

    cursor = await db.execute("""
        SELECT COALESCE(SUM(count), 0)
        FROM chickens
    """)

    total_chickens = int(
        (await cursor.fetchone())[0]
    )

    cursor = await db.execute("""
        SELECT COUNT(*)
        FROM deposits
        WHERE status = 'pending'
    """)

    pending_deposits = int(
        (await cursor.fetchone())[0]
    )

    cursor = await db.execute("""
        SELECT COUNT(*)
        FROM withdrawals
        WHERE status = 'pending'
    """)

    pending_withdrawals = int(
        (await cursor.fetchone())[0]
    )

    await cursor.close()
    await db.close()

    return {
        "total_users": total_users,
        "total_balance": total_balance,
        "total_eggs": total_eggs,
        "total_chickens": total_chickens,
        "pending_deposits": pending_deposits,
        "pending_withdrawals": pending_withdrawals
    }
