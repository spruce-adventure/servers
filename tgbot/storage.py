from tgbot.config import LOG_DIR
from tgbot.utils import now_iso


def log_action(user_id: int, name: str) -> None:
    with open(LOG_DIR / "actions.log", "a") as f:
        f.write(
            f"{now_iso()} | user={user_id} | created={name}\n"
        )


def log_error(text: str) -> None:
    with open(LOG_DIR / "errors.log", "a") as f:
        f.write(
            f"{now_iso()} | {text}\n"
        )
