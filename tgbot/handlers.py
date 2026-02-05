import subprocess
import tempfile
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from tgbot.auth import is_allowed
from tgbot.config import BASE_DIR
from tgbot.states import CreateConfig
from tgbot.storage import log_action, log_error
from tgbot.utils import sanitize_filename

router = Router()

WIREGUARD_CLIENTS = BASE_DIR.parent / "wireguard-clients.yml"
NEW_CLIENT_SCRIPT = BASE_DIR.parent / "new-client"


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать конфиг", callback_data="create_config")]
        ]
    )


def client_exists(name: str) -> bool:
    result = subprocess.run(
        ["grep", "-q", f"^{name}:", str(WIREGUARD_CLIENTS)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_new_client(name: str) -> str:
    result = subprocess.run(
        [str(NEW_CLIENT_SCRIPT), name],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "new-client failed").strip()
        raise RuntimeError(err)

    out = result.stdout.strip()
    if not out:
        raise RuntimeError("new-client returned empty output")

    return result.stdout


@router.message(F.text == "/start")
async def start(message: Message) -> None:
    await message.answer("Привет. Нажми кнопку ниже.", reply_markup=main_keyboard())


@router.callback_query(F.data == "create_config")
async def create_config(call: CallbackQuery, state: FSMContext) -> None:
    user_id = call.from_user.id

    if not is_allowed(user_id):
        await call.answer("❌ У тебя нет доступа", show_alert=True)
        return

    if call.message is None:
        await call.answer("Ок. Напиши /start заново.", show_alert=True)
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

    if client_exists(name):
        await message.answer("⚠️ Клиент с таким именем уже существует. Введи другое имя:")
        return

    tmp_path: Path | None = None

    try:
        conf_text = run_new_client(name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as tmp:
            tmp.write(conf_text)
            tmp_path = Path(tmp.name)

        await message.answer_document(FSInputFile(tmp_path, filename=f"{name}.conf"))

        if message.from_user is not None:
            log_action(message.from_user.id, name)
        else:
            log_action(-1, name)

    except Exception as e:
        log_error(str(e))
        await message.answer("❌ Ошибка при создании конфига")

    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
        await state.clear()
