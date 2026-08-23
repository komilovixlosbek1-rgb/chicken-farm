# database.py
# ============================================================
# 🐔 CHICKEN FARM DATABASE
# SQLite + aiosqlite
# Bot + Telegram Mini App uchun
# ============================================================

import time
import aiosqlite


DB_NAME = "chicken_farm_bot.db"


# ============================================================
# 🐔 TOVUQ SOZLAMALARI
# ============================================================

CHICKEN_CONFIG = {
    1: {
        "price": 1000,
        "egg_per_minute": 1,
        "name": "Lv.1 Tovuq",
    },
    2: {
        "price": 5000,
        "egg_per_minute": 3,
        "name": "Lv.2 Tovuq",
    },
    3: {
        "price": 15000,
        "egg_per_minute": 8,
        "name": "Lv.3 Tovuq",
    },
}


# ============================================================
# 🔧 DATABASE EXECUTE
# ============================================================

async def db_execute(
    query: str,
    params: tuple = ()
):
    async with aiosqlite.connect(
        DB_NAME,
        timeout=30
    ) as db:

        await db.execute(
            query,
            params
        )

        await db.commit()


async def db_fetch(
    query: str,
    params: tuple = (),
    fetchone: bool = False
):
    async with aiosqlite.connect(
        DB_NAME,
        timeout=30
    ) as db:

        async with db.execute(
            query,
            params
        ) as cursor:

            if fetchone:
                return await cursor.fetchone()

            return await cursor.fetchall()


# ============================================================
# 🚀 DATABASE INIT
# ============================================================

async def init_db():

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT DEFAULT '',
            balance INTEGER DEFAULT 0,
            egg_storage INTEGER DEFAULT 0,
            storage_capacity INTEGER DEFAULT 1000,
            has_deposited INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT 0
        )
        """
    )

    # --------------------------------------------------------
    # CHICKENS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS chickens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(user_id, level)
        )
        """
    )

    # --------------------------------------------------------
    # MINING
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS mining (
            user_id INTEGER PRIMARY KEY,
            last_claim INTEGER DEFAULT 0
        )
        """
    )

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    # --------------------------------------------------------
    # DEPOSIT REQUESTS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS deposit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            proof TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT 0,
            processed_at INTEGER DEFAULT 0
        )
        """
    )

    # --------------------------------------------------------
    # WITHDRAW REQUESTS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS withdraw_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            card_details TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT 0,
            processed_at INTEGER DEFAULT 0
        )
        """
    )

    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at INTEGER DEFAULT 0
        )
        """
    )

    # --------------------------------------------------------
    # DEFAULT SETTINGS
    # --------------------------------------------------------

    default_settings = {
        "card_number": "Kiritilmagan",
        "egg_exchange_rate": "10",
        "mining_reward": "100",
        "mining_cooldown": "3600",
        "min_deposit": "5000",
        "min_withdraw": "10000",
    }

    for key, value in default_settings.items():

        existing = await db_fetch(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,),
            fetchone=True
        )

        if not existing:

            await db_execute(
                """
                INSERT INTO settings
                (key, value)
                VALUES (?, ?)
                """,
                (key, value)
            )


# ============================================================
# 👤 USER YARATISH
# ============================================================

async def create_user(
    user_id: int,
    username: str = None,
    first_name: str = ""
):

    existing = await db_fetch(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    if existing:

        await db_execute(
            """
            UPDATE users
            SET username = ?,
                first_name = ?
            WHERE user_id = ?
            """,
            (
                username or "",
                first_name or "",
                user_id
            )
        )

        return

    await db_execute(
        """
        INSERT INTO users (
            user_id,
            username,
            first_name,
            balance,
            egg_storage,
            storage_capacity,
            has_deposited,
            created_at
        )
        VALUES (?, ?, ?, 0, 0, 1000, 0, ?)
        """,
        (
            user_id,
            username or "",
            first_name or "",
            int(time.time())
        )
    )


# ============================================================
# 👤 USER OLISH
# ============================================================

async def get_user(
    user_id: int
):

    row = await db_fetch(
        """
        SELECT
            user_id,
            username,
            first_name,
            balance,
            egg_storage,
            storage_capacity,
            has_deposited,
            created_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    if not row:

        await create_user(
            user_id
        )

        row = await db_fetch(
            """
            SELECT
                user_id,
                username,
                first_name,
                balance,
                egg_storage,
                storage_capacity,
                has_deposited,
                created_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
            fetchone=True
        )

    return {
        "user_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "balance": row[3],
        "egg_storage": row[4],
        "storage_capacity": row[5],
        "has_deposited": bool(row[6]),
        "created_at": row[7],
    }


# ============================================================
# 💰 BALANCE
# ============================================================

async def get_balance(
    user_id: int
):

    await create_user(
        user_id
    )

    row = await db_fetch(
        """
        SELECT balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    return int(
        row[0]
    ) if row else 0


async def change_balance(
    user_id: int,
    amount: int
):

    await create_user(
        user_id
    )

    await db_execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )


# ============================================================
# 🧾 TRANSACTION
# ============================================================

async def add_transaction(
    user_id: int,
    transaction_type: str,
    amount: int,
    description: str = ""
):

    await db_execute(
        """
        INSERT INTO transactions (
            user_id,
            type,
            amount,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            transaction_type,
            amount,
            description,
            int(time.time())
        )
    )


# ============================================================
# 🐔 TOVUQLAR
# ============================================================

async def get_chickens(
    user_id: int
):

    rows = await db_fetch(
        """
        SELECT
            level,
            count
        FROM chickens
        WHERE user_id = ?
        ORDER BY level ASC
        """,
        (user_id,)
    )

    result = []

    for level, count in rows:

        config = CHICKEN_CONFIG.get(
            level,
            {}
        )

        result.append({
            "level": level,
            "count": count,
            "price": config.get(
                "price",
                0
            ),
            "egg_per_minute": config.get(
                "egg_per_minute",
                0
            ),
            "name": config.get(
                "name",
                f"Lv.{level} Tovuq"
            )
        })

    return result


async def get_total_chickens(
    user_id: int
):

    row = await db_fetch(
        """
        SELECT COALESCE(SUM(count), 0)
        FROM chickens
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    return int(
        row[0] or 0
    )


# ============================================================
# 🛒 TOVUQ SOTIB OLISH
# ============================================================

async def buy_chicken(
    user_id: int,
    level: int
):

    if level not in CHICKEN_CONFIG:

        raise ValueError(
            "Noto'g'ri tovuq darajasi"
        )

    await create_user(
        user_id
    )

    config = CHICKEN_CONFIG[level]

    price = config["price"]

    balance = await get_balance(
        user_id
    )

    if balance < price:

        raise ValueError(
            "Balansingizda yetarli coin yo'q"
        )

    # Pulni ayirish
    await change_balance(
        user_id,
        -price
    )

    # Tovuqni qo'shish
    existing = await db_fetch(
        """
        SELECT id
        FROM chickens
        WHERE user_id = ?
        AND level = ?
        """,
        (
            user_id,
            level
        ),
        fetchone=True
    )

    if existing:

        await db_execute(
            """
            UPDATE chickens
            SET count = count + 1
            WHERE id = ?
            """,
            (
                existing[0],
            )
        )

    else:

        await db_execute(
            """
            INSERT INTO chickens (
                user_id,
                level,
                count
            )
            VALUES (?, ?, 1)
            """,
            (
                user_id,
                level
            )
        )

    await add_transaction(
        user_id,
        "buy_chicken",
        -price,
        f"Lv.{level} tovuq sotib olindi"
    )

    return {
        "level": level,
        "price": price,
        "balance": await get_balance(
            user_id
        ),
        "chickens": await get_chickens(
            user_id
        )
    }


# ============================================================
# 🥚 TUXUM OMBORI
# ============================================================

async def get_egg_storage(
    user_id: int
):

    await create_user(
        user_id
    )

    row = await db_fetch(
        """
        SELECT
            egg_storage,
            storage_capacity
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    eggs = int(
        row[0] or 0
    )

    capacity = int(
        row[1] or 1000
    )

    return {
        "eggs": eggs,
        "capacity": capacity,
        "percentage": round(
            eggs / capacity * 100,
            2
        ) if capacity else 0
    }


# ============================================================
# 🥚 TUXUM YIG'ISH / GENERATSIYA
# ============================================================

async def generate_eggs_for_user(
    user_id: int
):

    await create_user(
        user_id
    )

    user = await get_user(
        user_id
    )

    chickens = await get_chickens(
        user_id
    )

    total_per_minute = 0

    for chicken in chickens:

        total_per_minute += (
            chicken["egg_per_minute"]
            *
            chicken["count"]
        )

    if total_per_minute <= 0:

        return {
            "added": 0,
            "eggs": user["egg_storage"],
            "capacity": user["storage_capacity"]
        }

    # Hozirgi vaqtni ishlatamiz.
    # Oxirgi tuxum hisoblash vaqti uchun
    # alohida jadvaldan foydalanamiz.

    row = await db_fetch(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        (
            f"egg_last_{user_id}",
        ),
        fetchone=True
    )

    now = int(
        time.time()
    )

    if row:

        try:
            last_time = int(
                row[0]
            )
        except:
            last_time = now

    else:

        last_time = now

    elapsed_seconds = max(
        0,
        now - last_time
    )

    elapsed_minutes = elapsed_seconds // 60

    if elapsed_minutes <= 0:

        return {
            "added": 0,
            "eggs": user["egg_storage"],
            "capacity": user["storage_capacity"]
        }

    added = (
        total_per_minute
        *
        elapsed_minutes
    )

    current_eggs = user[
        "egg_storage"
    ]

    capacity = user[
        "storage_capacity"
    ]

    new_eggs = min(
        capacity,
        current_eggs + added
    )

    real_added = (
        new_eggs -
        current_eggs
    )

    await db_execute(
        """
        UPDATE users
        SET egg_storage = ?
        WHERE user_id = ?
        """,
        (
            new_eggs,
            user_id
        )
    )

    await db_execute(
        """
        INSERT OR REPLACE INTO settings
        (key, value)
        VALUES (?, ?)
        """,
        (
            f"egg_last_{user_id}",
            str(now)
        )
    )

    return {
        "added": real_added,
        "eggs": new_eggs,
        "capacity": capacity
    }


# ============================================================
# 🪙 TUXUM → COIN
# ============================================================

async def exchange_eggs(
    user_id: int
):

    await generate_eggs_for_user(
        user_id
    )

    row = await db_fetch(
        """
        SELECT egg_storage
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    eggs = int(
        row[0] or 0
    ) if row else 0

    if eggs <= 0:

        raise ValueError(
            "Omborda tuxum yo'q"
        )

    rate = int(
        await get_setting(
            "egg_exchange_rate",
            "10"
        )
    )

    coins = eggs // rate

    if coins <= 0:

        raise ValueError(
            f"Kamida {rate} ta tuxum kerak"
        )

    used_eggs = coins * rate

    remaining_eggs = (
        eggs -
        used_eggs
    )

    await db_execute(
        """
        UPDATE users
        SET egg_storage = ?,
            balance = balance + ?
        WHERE user_id = ?
        """,
        (
            remaining_eggs,
            coins,
            user_id
        )
    )

    await add_transaction(
        user_id,
        "egg_exchange",
        coins,
        f"{used_eggs} ta tuxum coinga almashtirildi"
    )

    return {
        "eggs_used": used_eggs,
        "remaining_eggs": remaining_eggs,
        "coins": coins,
        "balance": await get_balance(
            user_id
        )
    }


# ============================================================
# ⛏ MINING STATUS
# ============================================================

async def get_mining_status(
    user_id: int
):

    user = await get_user(
        user_id
    )

    if not user["has_deposited"]:

        return {
            "unlocked": False,
            "ready": False,
            "reward": 100,
            "remaining": 0,
            "next_claim_at": None
        }

    cooldown = int(
        await get_setting(
            "mining_cooldown",
            "3600"
        )
    )

    reward = int(
        await get_setting(
            "mining_reward",
            "100"
        )
    )

    row = await db_fetch(
        """
        SELECT last_claim
        FROM mining
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True
    )

    last_claim = int(
        row[0]
    ) if row else 0

    now = int(
        time.time()
    )

    elapsed = (
        now -
        last_claim
    )

    remaining = max(
        0,
        cooldown -
        elapsed
    )

    return {
        "unlocked": True,
        "ready": remaining <= 0,
        "reward": reward,
        "remaining": remaining,
        "next_claim_at": (
            now + remaining
            if remaining > 0
            else now
        )
    }


# ============================================================
# 🎁 MINING CLAIM
# ============================================================

async def claim_mining(
    user_id: int
):

    user = await get_user(
        user_id
    )

    if not user["has_deposited"]:

        raise ValueError(
            "Mining uchun avval depozit qiling"
        )

    status = await get_mining_status(
        user_id
    )

    if not status["ready"]:

        raise ValueError(
            "Mining bonusi hali tayyor emas"
        )

    reward = status[
        "reward"
    ]

    now = int(
        time.time()
    )

    await change_balance(
        user_id,
        reward
    )

    await db_execute(
        """
        INSERT OR REPLACE INTO mining (
            user_id,
            last_claim
        )
        VALUES (?, ?)
        """,
        (
            user_id,
            now
        )
    )

    await add_transaction(
        user_id,
        "mining",
        reward,
        "Mining bonus"
    )

    return {
        "reward": reward,
        "balance": await get_balance(
            user_id
        ),
        "claimed_at": now
    }


# ============================================================
# 🏠 DASHBOARD
# ============================================================

async def get_dashboard(
    user_id: int
):

    await generate_eggs_for_user(
        user_id
    )

    user = await get_user(
        user_id
    )

    chickens = await get_chickens(
        user_id
    )

    total_chickens = 0

    for chicken in chickens:

        total_chickens += (
            chicken["count"]
        )

    mining = await get_mining_status(
        user_id
    )

    return {
        "user": user,

        "balance": user[
            "balance"
        ],

        "eggs": user[
            "egg_storage"
        ],

        "egg_capacity": user[
            "storage_capacity"
        ],

        "total_chickens":
            total_chickens,

        "chickens":
            chickens,

        "mining":
            mining
    }


# ============================================================
# 💳 CARD
# ============================================================

async def get_card_number():

    return await get_setting(
        "card_number",
        "Kiritilmagan"
    )


# ============================================================
# ⚙️ SETTINGS
# ============================================================

async def get_setting(
    key: str,
    default: str = ""
):

    row = await db_fetch(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        (
            key,
        ),
        fetchone=True
    )

    if not row:

        return default

    return row[0]


async def update_setting(
    key: str,
    value: str
):

    await db_execute(
        """
        INSERT OR REPLACE INTO settings (
            key,
            value
        )
        VALUES (?, ?)
        """,
        (
            key,
            str(value)
        )
    )


# ============================================================
# 📥 DEPOSIT REQUEST
# ============================================================

async def create_deposit_request(
    user_id: int,
    amount: int,
    proof: str = ""
):

    min_amount = int(
        await get_setting(
            "min_deposit",
            "5000"
        )
    )

    if amount < min_amount:

        raise ValueError(
            f"Minimal depozit {min_amount} coin"
        )

    cursor_id = None

    async with aiosqlite.connect(
        DB_NAME,
        timeout=30
    ) as db:

        cursor = await db.execute(
            """
            INSERT INTO deposit_requests (
                user_id,
                amount,
                proof,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (
                user_id,
                amount,
                proof,
                int(time.time())
            )
        )

        cursor_id = cursor.lastrowid

        await db.commit()

    return cursor_id


# ============================================================
# 📤 WITHDRAW REQUEST
# ============================================================

async def create_withdraw_request(
    user_id: int,
    amount: int,
    card_details: str
):

    min_amount = int(
        await get_setting(
            "min_withdraw",
            "10000"
        )
    )

    if amount < min_amount:

        raise ValueError(
            f"Minimal chiqarish {min_amount} coin"
        )

    balance = await get_balance(
        user_id
    )

    if amount > balance:

        raise ValueError(
            "Balansda yetarli coin yo'q"
        )

    # Pulni vaqtincha bloklaymiz
    await change_balance(
        user_id,
        -amount
    )

    async with aiosqlite.connect(
        DB_NAME,
        timeout=30
    ) as db:

        cursor = await db.execute(
            """
            INSERT INTO withdraw_requests (
                user_id,
                amount,
                card_details,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (
                user_id,
                amount,
                card_details,
                int(time.time())
            )
        )

        request_id = cursor.lastrowid

        await db.commit()

    await add_transaction(
        user_id,
        "withdraw_pending",
        -amount,
        "Pul chiqarish so'rovi"
    )

    return request_id


# ============================================================
# 📜 TRANSACTIONS
# ============================================================

async def get_transactions(
    user_id: int,
    limit: int = 50
):

    rows = await db_fetch(
        """
        SELECT
            id,
            type,
            amount,
            description,
            created_at
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "type": row[1],
            "amount": row[2],
            "description": row[3],
            "created_at": row[4]
        })

    return result


# ============================================================
# 👨‍💼 ADMIN STATISTIKA
# ============================================================

async def get_admin_stats():

    users_row = await db_fetch(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(balance), 0),
            COALESCE(SUM(egg_storage), 0)
        FROM users
        """,
        fetchone=True
    )

    chickens_row = await db_fetch(
        """
        SELECT
            COALESCE(SUM(count), 0)
        FROM chickens
        """,
        fetchone=True
    )

    pending_deposits = await db_fetch(
        """
        SELECT COUNT(*)
        FROM deposit_requests
        WHERE status = 'pending'
        """,
        fetchone=True
    )

    pending_withdraws = await db_fetch(
        """
        SELECT COUNT(*)
        FROM withdraw_requests
        WHERE status = 'pending'
        """,
        fetchone=True
    )

    return {
        "users": int(
            users_row[0] or 0
        ),

        "total_balance": int(
            users_row[1] or 0
        ),

        "total_eggs": int(
            users_row[2] or 0
        ),

        "total_chickens": int(
            chickens_row[0] or 0
        ),

        "pending_deposits": int(
            pending_deposits[0] or 0
        ),

        "pending_withdraws": int(
            pending_withdraws[0] or 0
        )
    }


# ============================================================
# 🔄 DEPOSIT TASDIQLASH
# ============================================================

async def approve_deposit(
    request_id: int
):

    row = await db_fetch(
        """
        SELECT
            user_id,
            amount,
            status
        FROM deposit_requests
        WHERE id = ?
        """,
        (
            request_id,
        ),
        fetchone=True
    )

    if not row:

        raise ValueError(
            "Depozit so'rovi topilmadi"
        )

    user_id, amount, status = row

    if status != "pending":

        raise ValueError(
            "Bu so'rov allaqachon ko'rib chiqilgan"
        )

    await change_balance(
        user_id,
        amount
    )

    await db_execute(
        """
        UPDATE deposit_requests
        SET status = 'approved',
            processed_at = ?
        WHERE id = ?
        """,
        (
            int(time.time()),
            request_id
        )
    )

    await db_execute(
        """
        UPDATE users
        SET has_deposited = 1
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    await add_transaction(
        user_id,
        "deposit",
        amount,
        "Depozit tasdiqlandi"
    )

    return True


# ============================================================
# ❌ DEPOSIT RAD ETISH
# ============================================================

async def reject_deposit(
    request_id: int
):

    row = await db_fetch(
        """
        SELECT status
        FROM deposit_requests
        WHERE id = ?
        """,
        (
            request_id,
        ),
        fetchone=True
    )

    if not row:

        raise ValueError(
            "Depozit so'rovi topilmadi"
        )

    if row[0] != "pending":

        raise ValueError(
            "So'rov allaqachon ko'rib chiqilgan"
        )

    await db_execute(
        """
        UPDATE deposit_requests
        SET status = 'rejected',
            processed_at = ?
        WHERE id = ?
        """,
        (
            int(time.time()),
            request_id
        )
    )

    return True


# ============================================================
# 📤 WITHDRAW TASDIQLASH
# ============================================================

async def approve_withdraw(
    request_id: int
):

    row = await db_fetch(
        """
        SELECT status
        FROM withdraw_requests
        WHERE id = ?
        """,
        (
            request_id,
        ),
        fetchone=True
    )

    if not row:

        raise ValueError(
            "Withdraw so'rovi topilmadi"
        )

    if row[0] != "pending":

        raise ValueError(
            "So'rov allaqachon ko'rib chiqilgan"
        )

    await db_execute(
        """
        UPDATE withdraw_requests
        SET status = 'approved',
            processed_at = ?
        WHERE id = ?
        """,
        (
            int(time.time()),
            request_id
        )
    )

    return True


# ============================================================
# ❌ WITHDRAW RAD ETISH
# ============================================================

async def reject_withdraw(
    request_id: int
):

    row = await db_fetch(
        """
        SELECT
            user_id,
            amount,
            status
        FROM withdraw_requests
        WHERE id = ?
        """,
        (
            request_id,
        ),
        fetchone=True
    )

    if not row:

        raise ValueError(
            "Withdraw so'rovi topilmadi"
        )

    user_id, amount, status = row

    if status != "pending":

        raise ValueError(
            "So'rov allaqachon ko'rib chiqilgan"
        )

    # Pulni foydalanuvchiga qaytaramiz
    await change_balance(
        user_id,
        amount
    )

    await db_execute(
        """
        UPDATE withdraw_requests
        SET status = 'rejected',
            processed_at = ?
        WHERE id = ?
        """,
        (
            int(time.time()),
            request_id
        )
    )

    await add_transaction(
        user_id,
        "withdraw_rejected",
        amount,
        "Withdraw rad etildi va coin qaytarildi"
    )

    return True


# ============================================================
# 📦 PENDING REQUESTS
# ============================================================

async def get_pending_deposits():

    rows = await db_fetch(
        """
        SELECT
            id,
            user_id,
            amount,
            proof,
            created_at
        FROM deposit_requests
        WHERE status = 'pending'
        ORDER BY id DESC
        """
    )

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "amount": row[2],
            "proof": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]


async def get_pending_withdraws():

    rows = await db_fetch(
        """
        SELECT
            id,
            user_id,
            amount,
            card_details,
            created_at
        FROM withdraw_requests
        WHERE status = 'pending'
        ORDER BY id DESC
        """
    )

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "amount": row[2],
            "card_details": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]


# ============================================================
# 🐔 BACKGROUND EGG GENERATOR
# ============================================================

async def generate_all_eggs():

    users = await db_fetch(
        """
        SELECT user_id
        FROM users
        """
    )

    for row in users:

        try:

            await generate_eggs_for_user(
                row[0]
            )

        except Exception as e:

            print(
                f"Egg generator error "
                f"{row[0]}: {e}"
            )
