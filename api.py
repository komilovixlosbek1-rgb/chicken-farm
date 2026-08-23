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
    generate_eggs,
    exchange_eggs,
    claim_mining,
    create_deposit,
    create_withdraw,
)


# =========================================================
# ENVIRONMENT
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")


# =========================================================
# FASTAPI
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
# TELEGRAM INIT DATA
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

        user = json.loads(user_json)

        return user

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

def get_telegram_user(
    x_telegram_init_data: str
):

    return validate_telegram_data(
        x_telegram_init_data
    )


async def ensure_user(telegram_user):

    user_id = int(
        telegram_user["id"]
    )

    user = await get_user(
        user_id
    )

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

        user = await get_user(
            user_id
        )

    return user


# =========================================================
# MODELS
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
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {
        "status": "ok",
        "message": "🐔 Chicken Farm API ishlayapti!",
        "version": "2.0.0"
    }


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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    user = await ensure_user(
        telegram_user
    )

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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    user = await ensure_user(
        telegram_user
    )

    user_id = int(
        telegram_user["id"]
    )

    # Avtomatik tuxumlarni hisoblash
    await generate_eggs(
        user_id
    )

    user = await get_user(
        user_id
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
            user.get(
                "balance",
                0
            )
        ),

        "eggs": int(
            eggs
        ),

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
# FARM
# =========================================================

@app.get("/api/farm")
async def farm(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    user = await ensure_user(
        telegram_user
    )

    user_id = int(
        telegram_user["id"]
    )

    await generate_eggs(
        user_id
    )

    chickens = await get_chickens(
        user_id
    )

    eggs = await get_egg_storage(
        user_id
    )

    return {
        "success": True,
        "chickens": chickens,
        "eggs": eggs,
        "balance": user.get(
            "balance",
            0
        )
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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    user = await ensure_user(
        telegram_user
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
# EGGS
# =========================================================

@app.get("/api/eggs")
async def eggs(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    await ensure_user(
        telegram_user
    )

    user_id = int(
        telegram_user["id"]
    )

    await generate_eggs(
        user_id
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
# EXCHANGE EGGS
# =========================================================

@app.post("/api/eggs/exchange")
async def exchange(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    await ensure_user(
        telegram_user
    )

    user_id = int(
        telegram_user["id"]
    )

    await generate_eggs(
        user_id
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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    user = await ensure_user(
        telegram_user
    )

    last_claim = int(
        user.get(
            "last_mining",
            0
        )
    )

    now = int(
        time.time()
    )

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
        "can_claim": remaining == 0,
        "has_deposited": bool(
            user.get(
                "has_deposited",
                0
            )
        )
    }


@app.post("/api/mining/claim")
async def mining_claim(
    x_telegram_init_data: str = Header(
        default="",
        alias="X-Telegram-Init-Data"
    )
):

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    await ensure_user(
        telegram_user
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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    await ensure_user(
        telegram_user
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

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Depozit so'rovi yuborilmadi"
            )
        )

    return result


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

    telegram_user = get_telegram_user(
        x_telegram_init_data
    )

    await ensure_user(
        telegram_user
    )

    user_id = int(
        telegram_user["id"]
    )

    if data.amount < 10000:

        raise HTTPException(
            status_code=400,
            detail="Minimal chiqarish 10 000 coin"
        )

    if len(data.card.strip()) < 8:

        raise HTTPException(
            status_code=400,
            detail="Karta raqami noto'g'ri"
        )

    if len(data.name.strip()) < 2:

        raise HTTPException(
            status_code=400,
            detail="Ism-sharifni kiriting"
        )

    result = await create_withdraw(
        user_id=user_id,
        amount=data.amount,
        card=data.card.strip(),
        name=data.name.strip()
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
# CONFIG
# =========================================================

@app.get("/api/config")
async def config():

    settings = await get_settings()

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
# RUN LOCAL
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
