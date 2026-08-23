
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

# =========================================================
# SOZLAMALAR
# =========================================================

BOT_TOKEN = "8932236127:AAEHytxxo5S88GBL1HFN94BErEyid-O5Ue4"

MINI_APP_URL = "https://chicken-farm-630z.onrender.com"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# =========================================================
# BOT VA DISPATCHER
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start_command(message: Message):

    user = message.from_user

    first_name = user.first_name or "Fermer"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐔 Ferma",
                    web_app=WebAppInfo(
                        url=MINI_APP_URL
                    ),
                )
            ]
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
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():

    logging.info("🐔 Chicken Farm bot ishga tushmoqda...")

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
