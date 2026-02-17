from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:

    await state.clear()

    payload = (command.args or "").strip()
    if payload:
        logger.info("User %s started bot with payload=%r", message.from_user.id if message.from_user else None, payload)
    else:
        logger.info("User %s started bot", message.from_user.id if message.from_user else None)

    text = (
        "Привет! Я бот для генерации WireGuard-конфига.\n\n"
        "Что я умею:\n"
        "- создать новый конфиг по имени клиента\n"
        "- показать результат\n\n"
        "Напиши имя клиента одним сообщением (например: `liferooter-laptop`)."
    )

    await message.answer(text, parse_mode="Markdown")
