import re
from datetime import datetime


def sanitize_filename(name: str) -> str | None:
    name = name.strip()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        return None
    return name


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
