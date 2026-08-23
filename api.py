# api.py
import os
import time
import hmac
import hashlib
import json
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db,
    get_user,
    create_user,
    get_chickens,
    get_settings,
    buy_chicken,
    get_egg_storage,
    exchange_eggs,
    claim_mining,
    create_deposit,
    create_withdraw,
)


# =========================================================
# SOZLAMALAR
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

app = FastAPI(
    title="Chicken Farm Mini App API",
    version="1.0.0"
)

# Telegram Mini App uchun CORS
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
# TELEGRAM WEB APP INIT DATA TEKSHIRISH
# =========================================================

def validate_telegram_data(init_data: str):
    """
    Telegram WebApp yuborgan initData ni tekshiradi.
    BOT_TOKEN environment variable orqali beriladi.
    """

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData yuborilmadi"
        )

    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN serverda sozlanmagan"
        )

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))

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
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
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

        # auth_date tekshiruvi
        auth_date = int(parsed.get("auth_date", 0))

        if auth_date:
            # 24 soatdan eski ma'lumotni qabul qilmaymiz
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

        user = json.loads(user_json)

        return user

    except HTTPException:
        raise

    except Exception as e:
        print("Telegram validation error:", e)

        raise HTTPException(
            status_code=401,
            detail="Telegram ma'lumotlarini tekshirishda xato"
        )


# =========================================================
# HEADER ORQALI USER OLISH
# =========================================================

async def get_current_user(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):
    return validate_telegram_data(
        x_telegram_init_data
    )


# =========================================================
# MODELLAR
# =========================================================

class BuyChickenRequest(BaseModel):
    level: int


class DepositRequest(BaseModel):
    amount: int
    proof: str = ""


class WithdrawRequest(BaseModel):
    amount: int
    card: str
    name: str


# =========================================================
# TEST
# =========================================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "🐔 Chicken Farm API ishlayapti!"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


# =========================================================
# USER / DASHBOARD
# =========================================================

@app.get("/api/me")
async def me(
    user= None
):
    """
    Demo endpoint.
    Haqiqiy Telegram Mini App uchun
    /api/me-auth endpointidan foydalaniladi.
    """

    return {
        "message": "Telegram Mini App API"
    }


@app.post("/api/auth")
async def auth(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):
    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(telegram_user["id"])

    username = telegram_user.get(
        "username",
        ""
    )

    first_name = telegram_user.get(
        "first_name",
        ""
    )

    # User mavjud bo'lmasa yaratamiz
    user = await get_user(user_id)

    if not user:
        await create_user(
            user_id=user_id,
            username=username,
            first_name=first_name
        )

        user = await get_user(user_id)

    return {
        "success": True,
        "user": user
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

    chickens = await get_chickens(
        user_id
    )

    eggs = await get_egg_storage(
        user_id
    )

    settings = await get_settings()

    total_chickens = 0

    for chicken in chickens:
        total_chickens += int(
            chicken.get("count", 0)
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

        "settings": settings
    }


# =========================================================
# FERMA
# =========================================================

@app.get("/api/farm")
async def farm(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    chickens = await get_chickens(
        user_id
    )

    return {
        "success": True,
        "chickens": chickens
    }


# =========================================================
# TOVUQ SOTIB OLISH
# =========================================================

@app.post("/api/chicken/buy")
async def buy(
    data: BuyChickenRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    if data.level not in [1, 2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Tovuq darajasi noto'g'ri"
        )

    result = await buy_chicken(
        user_id=user_id,
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
# TUXUM OMBORI
# =========================================================

@app.get("/api/eggs")
async def eggs(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    user = await get_user(
        user_id
    )

    egg_count = await get_egg_storage(
        user_id
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
# TUXUMLARNI COINGA ALMASHTIRISH
# =========================================================

@app.post("/api/eggs/exchange")
async def exchange(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    result = await exchange_eggs(
        user_id
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

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    user = await get_user(
        user_id
    )

    last_claim = int(
        user.get(
            "last_mining",
            0
        )
    )

    now = int(time.time())

    cooldown = 3600

    remaining = max(
        0,
        cooldown - (
            now - last_claim
        )
    )

    return {
        "success": True,
        "bonus": 100,
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

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    result = await claim_mining(
        user_id
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
# DEPOZIT
# =========================================================

@app.post("/api/deposit")
async def deposit(
    data: DepositRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    if data.amount < 5000:
        raise HTTPException(
            status_code=400,
            detail="Minimal depozit 5 000 coin"
        )

    result = await create_deposit(
        user_id=user_id,
        amount=data.amount,
        proof=data.proof
    )

    return result


# =========================================================
# PUL CHIQARISH
# =========================================================

@app.post("/api/withdraw")
async def withdraw(
    data: WithdrawRequest,
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = validate_telegram_data(
        x_telegram_init_data
    )

    user_id = int(
        telegram_user["id"]
    )

    if data.amount < 10000:
        raise HTTPException(
            status_code=400,
            detail="Minimal chiqarish 10 000 coin"
        )

    if len(data.card) < 8:
        raise HTTPException(
            status_code=400,
            detail="Karta raqami noto'g'ri"
        )

    if len(data.name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ism-sharifni kiriting"
        )

    result = await create_withdraw(
        user_id=user_id,
        amount=data.amount,
        card=data.card,
        name=data.name
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Pul chiqarish so'rovi yuborilmadi"
            )
        )

    return result


# =========================================================
# BOTGA ULASH UCHUN MA'LUMOT
# =========================================================

@app.get("/api/config")
async def config():

    return {
        "app_name": "Chicken Farm",
        "currency": "coin",

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

        "egg_exchange_rate": 10,

        "mining": {
            "bonus": 100,
            "cooldown": 3600
        },

        "deposit_min": 5000,
        "withdraw_min": 10000
    }


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", 8000)
        ),
        reload=False
    )
