import os
from pathlib import Path
from typing import Final

BASE_DIR = Path(__file__).resolve().parent

_raw_token = os.getenv("BOT_TOKEN")
if _raw_token is None:
    raise RuntimeError("BOT_TOKEN is not set")

BOT_TOKEN: Final[str] = _raw_token

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

WHITELIST_PATH = BASE_DIR / "whitelist.json"
