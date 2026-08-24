import os
import time
import hmac
import hashlib
import json
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import (
    init_db,
    get_user,
    create_user,
    get_chickens,
    get_settings,
    set_setting,
    buy_chicken,
    get_egg_storage,
    exchange_eggs,
    claim_mining,
    create_deposit,
    create_withdraw,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip())
except Exception:
    ADMIN_ID = 0


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Chicken Farm Mini App API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup():
    await init_db()


# =========================================================
# TELEGRAM VALIDATION
# =========================================================

def validate_telegram_data(init_data: str):

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData yuborilmadi"
        )

    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN Render Environment Variables'da sozlanmagan"
        )

    try:

        parsed = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )

        received_hash = parsed.pop("hash", None)

        if not received_hash:
            raise HTTPException(
                status_code=401,
                detail="Telegram hash mavjud emas"
            )

        data_check_string = "\n".join(
            f"{key}={parsed[key]}"
            for key in sorted(parsed.keys())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Telegram initData noto'g'ri"
            )

        auth_date = int(
            parsed.get("auth_date", 0)
        )

        if auth_date:
            if time.time() - auth_date > 86400:
                raise HTTPException(
                    status_code=401,
                    detail="Telegram sessiyasi eskirgan"
                )

        user_json = parsed.get("user")

        if not user_json:
            raise HTTPException(
                status_code=401,
                detail="Telegram user ma'lumoti topilmadi"
            )

        return json.loads(user_json)

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Telegram validation error:",
            repr(e)
        )

        raise HTTPException(
            status_code=401,
            detail="Telegram ma'lumotlarini tekshirishda xato"
        )


# =========================================================
# USER AUTH
# =========================================================

async def get_current_user(
    x_telegram_init_data: str
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    user = await get_user(user_id)

    if not user:

        await create_user(
            user_id=user_id,
            username=telegram_user.get(
                "username",
                ""
            ),
            first_name=telegram_user.get(
                "first_name",
                ""
            )
        )

        user = await get_user(user_id)

    return telegram_user, user


# =========================================================
# ADMIN CHECK
# =========================================================

def check_admin(telegram_user):

    if ADMIN_ID <= 0:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_ID Render Environment Variables'da sozlanmagan"
        )

    user_id = int(
        telegram_user["id"]
    )

    if user_id != ADMIN_ID:
        raise HTTPException(
            status_code=403,
            detail="Bu bo'lim faqat admin uchun"
        )

    return True


async def get_admin(
    x_telegram_init_data: str
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    check_admin(telegram_user)

    return telegram_user


# =========================================================
# REQUEST MODELS
# =========================================================

class BuyChickenRequest(BaseModel):
    level: int


class DepositRequest(BaseModel):
    amount: int
    proof: str = ""
    crypto: str = "ETH"
    tx_hash: str = ""


class WithdrawRequest(BaseModel):
    amount: int
    card: str = ""
    name: str
    crypto: str = ""
    wallet: str = ""


class AdminBalanceRequest(BaseModel):
    user_id: int
    amount: int


class AdminChickenRequest(BaseModel):
    user_id: int
    level: int
    count: int


class AdminSettingRequest(BaseModel):
    key: str
    value: str


class AdminDepositAction(BaseModel):
    deposit_id: int


class AdminWithdrawAction(BaseModel):
    withdraw_id: int


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }


# =========================================================
# AUTH
# =========================================================

@app.post("/api/auth")
async def auth(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    return {
        "success": True,
        "user": user,
        "is_admin": int(
            telegram_user["id"]
        ) == ADMIN_ID
    }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/api/dashboard")
async def dashboard(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    chickens = await get_chickens(
        user_id
    )

    eggs = await get_egg_storage(
        user_id
    )

    settings = await get_settings()

    total_chickens = sum(
        int(chicken.get("count", 0))
        for chicken in chickens
    )

    return {
        "success": True,

        "user": user,

        "balance": int(
            user.get("balance", 0)
        ),

        "eggs": int(eggs),

        "egg_capacity": int(
            user.get(
                "storage_capacity",
                1000
            )
        ),

        "total_chickens": total_chickens,

        "chickens": chickens,

        "settings": settings,

        "is_admin": int(
            telegram_user["id"]
        ) == ADMIN_ID
    }


# =========================================================
# FARM
# =========================================================

@app.get("/api/farm")
async def farm(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    chickens = await get_chickens(
        int(telegram_user["id"])
    )

    return {
        "success": True,
        "chickens": chickens
    }


# =========================================================
# BUY CHICKEN
# =========================================================

@app.post("/api/chicken/buy")
async def buy(
    data: BuyChickenRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    if data.level not in [1, 2, 3]:

        raise HTTPException(
            status_code=400,
            detail="Tovuq darajasi noto'g'ri"
        )

    result = await buy_chicken(
        user_id=int(
            telegram_user["id"]
        ),
        level=data.level
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Tovuq sotib olib bo'lmadi"
            )
        )

    return result


# =========================================================
# EGGS
# =========================================================

@app.get("/api/eggs")
async def eggs(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    egg_count = await get_egg_storage(
        int(telegram_user["id"])
    )

    return {
        "success": True,
        "eggs": egg_count,
        "capacity": user.get(
            "storage_capacity",
            1000
        )
    }


# =========================================================
# EXCHANGE EGGS
# =========================================================

@app.post("/api/eggs/exchange")
async def exchange(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    result = await exchange_eggs(
        int(telegram_user["id"])
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Almashtirish amalga oshmadi"
            )
        )

    return result


# =========================================================
# MINING
# =========================================================

@app.get("/api/mining")
async def mining(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    last_claim = int(
        user.get("last_mining", 0)
    )

    now = int(time.time())

    settings = await get_settings()

    cooldown = int(
        settings.get(
            "mining_cooldown",
            3600
        )
    )

    bonus = int(
        settings.get(
            "mining_bonus",
            100
        )
    )

    remaining = max(
        0,
        cooldown - (
            now - last_claim
        )
    )

    return {
        "success": True,
        "bonus": bonus,
        "cooldown": cooldown,
        "remaining": remaining,
        "can_claim": remaining == 0
    }


@app.post("/api/mining/claim")
async def mining_claim(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    result = await claim_mining(
        int(telegram_user["id"])
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Mining bonusini olib bo'lmadi"
            )
        )

    return result


# =========================================================
# DEPOSIT
# =========================================================

@app.post("/api/deposit")
async def deposit(
    data: DepositRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    if data.amount < 5000:

        raise HTTPException(
            status_code=400,
            detail="Minimal depozit 5 000 coin"
        )

    crypto = (
        data.crypto or "ETH"
    ).upper()

    if crypto != "ETH":

        raise HTTPException(
            status_code=400,
            detail="Hozircha faqat Ethereum (ETH) qabul qilinadi"
        )

    if not data.tx_hash.strip() and not data.proof.strip():

        raise HTTPException(
            status_code=400,
            detail="ETH transaction hash yoki to'lov isbotini kiriting"
        )

    result = await create_deposit(
        user_id=int(
            telegram_user["id"]
        ),
        amount=data.amount,
        proof=data.proof.strip()
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Depozit yaratilmadi"
            )
        )

    return {
        **result,
        "crypto": "ETH",
        "tx_hash": data.tx_hash.strip()
    }


# =========================================================
# WITHDRAW
# =========================================================

@app.post("/api/withdraw")
async def withdraw(
    data: WithdrawRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user, user = await get_current_user(
        x_telegram_init_data
    )

    if data.amount < 10000:

        raise HTTPException(
            status_code=400,
            detail="Minimal chiqarish 10 000 coin"
        )

    name = data.name.strip()

    if len(name) < 2:

        raise HTTPException(
            status_code=400,
            detail="Ism-sharifni kiriting"
        )

    crypto = (
        data.crypto or "ETH"
    ).upper()

    if crypto != "ETH":

        raise HTTPException(
            status_code=400,
            detail="Hozircha faqat Ethereum (ETH) orqali chiqarish mumkin"
        )

    wallet = data.wallet.strip()

    if not wallet:

        raise HTTPException(
            status_code=400,
            detail="Ethereum wallet manzilini kiriting"
        )

    if not wallet.startswith("0x") or len(wallet) != 42:

        raise HTTPException(
            status_code=400,
            detail="Ethereum wallet manzili noto'g'ri"
        )

    result = await create_withdraw(
        user_id=int(
            telegram_user["id"]
        ),
        amount=data.amount,
        card=wallet,
        name=name
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Pul chiqarish so'rovi yuborilmadi"
            )
        )

    return {
        **result,
        "crypto": "ETH",
        "wallet": wallet
    }


# =========================================================
# CONFIG
# =========================================================

@app.get("/api/config")
async def config():

    settings = await get_settings()

    return {
        "app_name": "Chicken Farm",
        "currency": "coin",

        "crypto": {
            "deposit": ["ETH"],
            "withdraw": ["ETH"],
            "name": "Ethereum",
            "symbol": "ETH"
        },

        "chickens": {
            "1": {
                "name": "Lv.1 Tovuq",
                "price": 1000
            },
            "2": {
                "name": "Lv.2 Tovuq",
                "price": 5000
            },
            "3": {
                "name": "Lv.3 Tovuq",
                "price": 15000
            }
        },

        "egg_exchange_rate": int(
            settings.get(
                "egg_exchange_rate",
                10
            )
        ),

        "mining": {
            "bonus": int(
                settings.get(
                    "mining_bonus",
                    100
                )
            ),
            "cooldown": int(
                settings.get(
                    "mining_cooldown",
                    3600
                )
            )
        },

        "deposit_min": 5000,

        "withdraw_min": 10000
    }


# =========================================================
# ADMIN
# =========================================================

@app.get("/api/admin")
async def admin_panel(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    settings = await get_settings()

    return {
        "success": True,
        "admin": True,
        "settings": settings
    }


# =========================================================
# ADMIN SETTINGS
# =========================================================

@app.post("/api/admin/setting")
async def admin_setting(
    data: AdminSettingRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    allowed = {
        "card_number",
        "eth_deposit_address",
        "eth_withdraw_address",
        "egg_exchange_rate",
        "mining_bonus",
        "mining_cooldown",
        "chicken_price_1",
        "chicken_price_2",
        "chicken_price_3"
    }

    if data.key not in allowed:

        raise HTTPException(
            status_code=400,
            detail="Bu sozlamani o'zgartirish mumkin emas"
        )

    if not str(data.value).strip():

        raise HTTPException(
            status_code=400,
            detail="Qiymat bo'sh bo'lmasin"
        )

    await set_setting(
        data.key,
        str(data.value).strip()
    )

    return {
        "success": True,
        "message": "Sozlama muvaffaqiyatli o'zgartirildi",
        "key": data.key,
        "value": data.value
    }


# =========================================================
# ADMIN BALANCE ADD
# =========================================================

@app.post("/api/admin/balance/add")
async def admin_balance_add(
    data: AdminBalanceRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    if data.amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Miqdor 0 dan katta bo'lishi kerak"
        )

    user = await get_user(
        data.user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi"
        )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    await db.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """,
        (
            data.amount,
            data.user_id
        )
    )

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": f"+{data.amount} coin qo'shildi"
    }


# =========================================================
# ADMIN BALANCE REMOVE
# =========================================================

@app.post("/api/admin/balance/remove")
async def admin_balance_remove(
    data: AdminBalanceRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    if data.amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Miqdor 0 dan katta bo'lishi kerak"
        )

    user = await get_user(
        data.user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi"
        )

    balance = int(
        user.get("balance", 0)
    )

    if balance < data.amount:

        raise HTTPException(
            status_code=400,
            detail="Foydalanuvchi balansida buncha coin yo'q"
        )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    await db.execute(
        """
        UPDATE users
        SET balance = balance - ?
        WHERE user_id = ?
        """,
        (
            data.amount,
            data.user_id
        )
    )

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": f"-{data.amount} coin olib tashlandi"
    }


# =========================================================
# ADMIN GIVE CHICKEN
# =========================================================

@app.post("/api/admin/chicken/give")
async def admin_give_chicken(
    data: AdminChickenRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    if data.level not in [1, 2, 3]:

        raise HTTPException(
            status_code=400,
            detail="Lv noto'g'ri"
        )

    if data.count <= 0:

        raise HTTPException(
            status_code=400,
            detail="Tovuq soni 0 dan katta bo'lishi kerak"
        )

    user = await get_user(
        data.user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi"
        )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    await db.execute(
        """
        INSERT INTO chickens
            (user_id, level, count)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, level)
        DO UPDATE SET count = count + excluded.count
        """,
        (
            data.user_id,
            data.level,
            data.count
        )
    )

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": f"Lv.{data.level} dan {data.count} ta tovuq berildi"
    }


# =========================================================
# ADMIN REMOVE CHICKEN
# =========================================================

@app.post("/api/admin/chicken/remove")
async def admin_remove_chicken(
    data: AdminChickenRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    if data.level not in [1, 2, 3]:

        raise HTTPException(
            status_code=400,
            detail="Lv noto'g'ri"
        )

    if data.count <= 0:

        raise HTTPException(
            status_code=400,
            detail="Tovuq soni noto'g'ri"
        )

    user = await get_user(
        data.user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi"
        )

    chickens = await get_chickens(
        data.user_id
    )

    current = 0

    for chicken in chickens:

        if int(
            chicken["level"]
        ) == data.level:

            current = int(
                chicken["count"]
            )

    if current < data.count:

        raise HTTPException(
            status_code=400,
            detail="Foydalanuvchida buncha tovuq yo'q"
        )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    new_count = current - data.count

    if new_count <= 0:

        await db.execute(
            """
            DELETE FROM chickens
            WHERE user_id = ?
            AND level = ?
            """,
            (
                data.user_id,
                data.level
            )
        )

    else:

        await db.execute(
            """
            UPDATE chickens
            SET count = ?
            WHERE user_id = ?
            AND level = ?
            """,
            (
                new_count,
                data.user_id,
                data.level
            )
        )

    await db.commit()
    await db.close()

    return {
        "success": True,
        "message": f"Lv.{data.level} dan {data.count} ta tovuq olib tashlandi"
    }


# =========================================================
# ADMIN USERS
# =========================================================

@app.get("/api/admin/users")
async def admin_users(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
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
        """
    )

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    users = []

    for row in rows:

        users.append({
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "balance": int(row[3]),
            "eggs": int(row[4]),
            "has_deposited": int(row[5]),
            "created_at": int(row[6])
        })

    return {
        "success": True,
        "count": len(users),
        "users": users
    }


# =========================================================
# ADMIN STATISTICS
# =========================================================

@app.get("/api/admin/stats")
async def admin_stats(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(balance), 0)
        FROM users
        """
    )

    users_row = await cursor.fetchone()

    cursor2 = await db.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(amount), 0)
        FROM deposits
        WHERE status = 'pending'
        """
    )

    deposits_row = await cursor2.fetchone()

    cursor3 = await db.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(amount), 0)
        FROM withdrawals
        WHERE status = 'pending'
        """
    )

    withdrawals_row = await cursor3.fetchone()

    cursor4 = await db.execute(
        """
        SELECT COALESCE(SUM(count), 0)
        FROM chickens
        """
    )

    chickens_row = await cursor4.fetchone()

    cursor5 = await db.execute(
        """
        SELECT COALESCE(SUM(eggs), 0)
        FROM users
        """
    )

    eggs_row = await cursor5.fetchone()

    await cursor.close()
    await cursor2.close()
    await cursor3.close()
    await cursor4.close()
    await cursor5.close()
    await db.close()

    return {
        "success": True,

        "users": int(
            users_row[0]
        ),

        "total_balance": int(
            users_row[1]
        ),

        "pending_deposits": int(
            deposits_row[0]
        ),

        "pending_deposit_amount": int(
            deposits_row[1]
        ),

        "pending_withdrawals": int(
            withdrawals_row[0]
        ),

        "pending_withdraw_amount": int(
            withdrawals_row[1]
        ),

        "total_chickens": int(
            chickens_row[0]
        ),

        "total_eggs": int(
            eggs_row[0]
        )
    }


# =========================================================
# ADMIN DEPOSITS
# =========================================================

@app.get("/api/admin/deposits")
async def admin_deposits(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT
            id,
            user_id,
            amount,
            proof,
            status,
            created_at
        FROM deposits
        ORDER BY id DESC
        """
    )

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return {
        "success": True,
        "deposits": [
            {
                "id": row[0],
                "user_id": row[1],
                "amount": int(row[2]),
                "proof": row[3],
                "status": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    }


# =========================================================
# ADMIN DEPOSIT APPROVE
# =========================================================

@app.post("/api/admin/deposit/approve")
async def admin_deposit_approve(
    data: AdminDepositAction,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT
            user_id,
            amount,
            status
        FROM deposits
        WHERE id = ?
        """,
        (
            data.deposit_id,
        )
    )

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=404,
            detail="Depozit topilmadi"
        )

    user_id = int(row[0])
    amount = int(row[1])
    status = row[2]

    if status != "pending":

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=400,
            detail="Bu depozit allaqachon ko'rib chiqilgan"
        )

    await db.execute(
        """
        UPDATE users
        SET
            balance = balance + ?,
            has_deposited = 1
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )

    await db.execute(
        """
        UPDATE deposits
        SET status = 'approved'
        WHERE id = ?
        """,
        (
            data.deposit_id,
        )
    )

    await db.commit()
    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"Depozit tasdiqlandi: +{amount} coin"
    }


# =========================================================
# ADMIN DEPOSIT REJECT
# =========================================================

@app.post("/api/admin/deposit/reject")
async def admin_deposit_reject(
    data: AdminDepositAction,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT status
        FROM deposits
        WHERE id = ?
        """,
        (
            data.deposit_id,
        )
    )

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=404,
            detail="Depozit topilmadi"
        )

    if row[0] != "pending":

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=400,
            detail="Bu depozit allaqachon ko'rib chiqilgan"
        )

    await db.execute(
        """
        UPDATE deposits
        SET status = 'rejected'
        WHERE id = ?
        """,
        (
            data.deposit_id,
        )
    )

    await db.commit()
    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Depozit rad etildi"
    }


# =========================================================
# ADMIN WITHDRAWS
# =========================================================

@app.get("/api/admin/withdrawals")
async def admin_withdrawals(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT
            id,
            user_id,
            amount,
            card,
            name,
            status,
            created_at
        FROM withdrawals
        ORDER BY id DESC
        """
    )

    rows = await cursor.fetchall()

    await cursor.close()
    await db.close()

    return {
        "success": True,

        "withdrawals": [
            {
                "id": row[0],
                "user_id": row[1],
                "amount": int(row[2]),
                "wallet": row[3],
                "name": row[4],
                "crypto": "ETH",
                "status": row[5],
                "created_at": row[6]
            }
            for row in rows
        ]
    }


# =========================================================
# ADMIN WITHDRAW APPROVE
# =========================================================

@app.post("/api/admin/withdraw/approve")
async def admin_withdraw_approve(
    data: AdminWithdrawAction,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT
            user_id,
            amount,
            status
        FROM withdrawals
        WHERE id = ?
        """,
        (
            data.withdraw_id,
        )
    )

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=404,
            detail="Withdraw topilmadi"
        )

    if row[2] != "pending":

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=400,
            detail="Bu withdraw allaqachon ko'rib chiqilgan"
        )

    await db.execute(
        """
        UPDATE withdrawals
        SET status = 'approved'
        WHERE id = ?
        """,
        (
            data.withdraw_id,
        )
    )

    await db.commit()
    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": "Withdraw tasdiqlandi"
    }


# =========================================================
# ADMIN WITHDRAW REJECT
# =========================================================

@app.post("/api/admin/withdraw/reject")
async def admin_withdraw_reject(
    data: AdminWithdrawAction,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    import aiosqlite

    db = await aiosqlite.connect(
        "chicken_farm.db"
    )

    cursor = await db.execute(
        """
        SELECT
            user_id,
            amount,
            status
        FROM withdrawals
        WHERE id = ?
        """,
        (
            data.withdraw_id,
        )
    )

    row = await cursor.fetchone()

    if not row:

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=404,
            detail="Withdraw topilmadi"
        )

    user_id = int(row[0])
    amount = int(row[1])
    status = row[2]

    if status != "pending":

        await cursor.close()
        await db.close()

        raise HTTPException(
            status_code=400,
            detail="Bu withdraw allaqachon ko'rib chiqilgan"
        )

    await db.execute(
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

    await db.execute(
        """
        UPDATE withdrawals
        SET status = 'rejected'
        WHERE id = ?
        """,
        (
            data.withdraw_id,
        )
    )

    await db.commit()
    await cursor.close()
    await db.close()

    return {
        "success": True,
        "message": f"Withdraw rad etildi. {amount} coin foydalanuvchiga qaytarildi"
    }


# =========================================================
# ADMIN ETH ADDRESS
# =========================================================

@app.get("/api/admin/crypto")
async def admin_crypto(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    await get_admin(
        x_telegram_init_data
    )

    settings = await get_settings()

    return {
        "success": True,
        "crypto": {
            "name": "Ethereum",
            "symbol": "ETH",
            "deposit_address": settings.get(
                "eth_deposit_address",
                ""
            ),
            "withdraw_address": settings.get(
                "eth_withdraw_address",
                ""
            )
        }
    }


# =========================================================
# PUBLIC ETH DEPOSIT ADDRESS
# =========================================================

@app.get("/api/crypto")
async def crypto():

    settings = await get_settings()

    return {
        "success": True,

        "ethereum": {
            "name": "Ethereum",
            "symbol": "ETH",
            "deposit_address": settings.get(
                "eth_deposit_address",
                ""
            )
        }
    }


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "8000"
            )
        )
    )
