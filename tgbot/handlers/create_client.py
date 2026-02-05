import asyncio
import logging
import tempfile
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from tgbot.auth import is_allowed
from tgbot.config import GITHUB_ENABLED
from tgbot.states import CreateConfig
from tgbot.utils import sanitize_filename
from tgbot.services.repo import (
    RepoLock,
    client_exists,
    run_new_client,
    git_has_changes,
    git_commit_and_push,
)
from tgbot.services.github_actions import notify_pipeline

logger = logging.getLogger("tgbot")
router = Router()


@router.callback_query(F.data == "create_config")
async def create_config(call: CallbackQuery, state: FSMContext) -> None:
    user_id = call.from_user.id

    if not is_allowed(user_id):
        await call.answer("❌ У тебя нет доступа", show_alert=True)
        return

    if call.message is None:
        await call.answer("Напиши /start еще раз.", show_alert=True)
        return

    await call.message.answer("Введите имя клиента (без .conf):")
    await state.set_state(CreateConfig.waiting_for_name)


@router.message(CreateConfig.waiting_for_name)
async def receive_name(message: Message, state: FSMContext) -> None:
    text = message.text
    if not text:
        await message.answer("Отправь текст с именем клиента (без .conf).")
        return

    raw_name = text.strip()
    name = sanitize_filename(raw_name)
    if not name:
        await message.answer("❌ Недопустимое имя. Используй латиницу, цифры, _ и -")
        return

    if message.from_user is None:
        await message.answer("❌ Не могу определить отправителя.")
        return

    user_id = message.from_user.id
    tmp_path: Path | None = None

    try:
        with RepoLock():
            if client_exists(name):
                await message.answer(
                    "⚠️ Клиент с таким именем уже существует. Введи другое имя:"
                )
                return

            logger.info("start create client=%s tg=%s", name, user_id)
            conf_text = run_new_client(name)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as tmp:
                tmp.write(conf_text)
                tmp_path = Path(tmp.name)

            await message.answer_document(
                FSInputFile(tmp_path, filename=f"{name}.conf")
            )

            if not git_has_changes():
                logger.warning("no git changes after new-client client=%s", name)
                await message.answer(
                    "⚠️ new-client не изменил репозиторий. Конфиг отправил, пушить нечего."
                )
                return

            sha = git_commit_and_push(name, user_id)
            await message.answer(
                "🟡 Изменения запушены. Жду завершения пайплайна и отпишу сюда."
            )

            if GITHUB_ENABLED:
                asyncio.create_task(notify_pipeline(message, sha))
            else:
                await message.answer(
                    "ℹ️ GitHub-проверка отключена (нет GITHUB_* переменных)."
                )

            logger.info("client created client=%s tg=%s sha=%s", name, user_id, sha)

    except Exception as e:
        logger.exception("failed creating client=%s tg=%s", name, user_id)
        await message.answer(f"❌ Ошибка: {e}")

    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
        await state.clear()
