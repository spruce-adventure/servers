from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать конфиг", callback_data="create_config")]
        ]
    )


@router.message(F.text == "/start")
async def start(message: Message) -> None:
    await message.answer("Привет. Нажми кнопку ниже.", reply_markup=main_keyboard())
