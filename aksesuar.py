"""
Telegram bot: mijozlardan mahsulot rasmi + ma'lumot qabul qiladi
va tasdiqlangandan so'ng belgilangan ADMIN_ID'ga yuboradi.

O'RNATISH:
    pip install aiogram

ISHGA TUSHIRISH:
    1. BOT_TOKEN va ADMIN_ID ni muhit o'zgaruvchisi (environment variable)
       sifatida bering (Railway'da Variables bo'limida)
    2. python mijoz_bot.py

ISHLASH TARTIBI:
    1. Mijoz botga /start bosadi -> bot "qaysi tavar kerak" deb so'raydi
    2. Mijoz mahsulot rasmini caption (ism, telefon va h.k.) bilan yuboradi
    3. Bot "Yuborish" tugmasini chiqaradi
    4. Mijoz tugmani bosgach, rasm + ma'lumot ADMIN_ID'ga
       "Mijoz yozdi!" deb yuboriladi
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ============ SOZLAMALAR ============
# Railway'da bularni kodga yozmaymiz, "Variables" bo'limiga qo'shamiz:
#   BOT_TOKEN = @BotFather'dan olingan token
#   ADMIN_ID  = habarlar boradigan odamning Telegram ID raqami
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
# =====================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Order(StatesGroup):
    waiting_photo = State()
    confirm = State()


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yuborish", callback_data="send_order")],
            [InlineKeyboardButton(text="🔄 Qayta yuborish", callback_data="restart_order")],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Order.waiting_photo)
    await message.answer(
        "Assalomu alekum! Sizga qaysi tavar kerak?\n\n"
        "Iltimos, kerakli mahsulotning rasmini va o'zingiz haqingizda "
        "(ism, telefon raqam va h.k.) ma'lumotni bitta xabarda birga yuboring."
    )


@dp.message(Order.waiting_photo, F.photo)
async def photo_handler(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    caption = message.caption or "(izoh yozilmagan)"

    await state.update_data(photo_id=photo_id, caption=caption)
    await state.set_state(Order.confirm)

    await message.answer(
        "Ma'lumotlaringiz qabul qilindi. Yuborishni tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
    )


@dp.message(Order.waiting_photo)
async def wrong_content_handler(message: Message) -> None:
    await message.answer("Iltimos, mahsulot rasmini (izoh bilan birga) yuboring.")


@dp.callback_query(Order.confirm, F.data == "send_order")
async def send_order_handler(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    photo_id = data.get("photo_id")
    caption = data.get("caption")

    user = callback.from_user
    username = f"@{user.username}" if user.username else "yo'q"

    admin_caption = (
        "🆕 Mijoz yozdi!\n\n"
        f"👤 Ism: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"✍️ Xabar: {caption}"
    )

    await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_caption)

    await callback.message.edit_text(
        "✅ Arizangiz muvaffaqiyatli yuborildi. Tez orada siz bilan bog'lanishadi!"
    )
    await state.clear()
    await callback.answer()


@dp.callback_query(Order.confirm, F.data == "restart_order")
async def restart_order_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Order.waiting_photo)
    await callback.message.edit_text(
        "Yaxshi, qaytadan mahsulot rasmini va ma'lumotingizni yuboring."
    )
    await callback.answer()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
