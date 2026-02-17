import os
from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent

# --- Telegram ---

_bot_token = os.getenv("BOT_TOKEN")
if _bot_token is None:
    raise RuntimeError("BOT_TOKEN is not set")

BOT_TOKEN: Final[str] = _bot_token


# --- Paths ---

WHITELIST_PATH: Final[Path] = BASE_DIR / "whitelist.json"


# --- Repo (commit/push) ---

_repo_dir_env = os.getenv("REPO_DIR")

if _repo_dir_env is not None:
    _repo_dir = Path(_repo_dir_env).resolve()
else:
    _repo_dir = (BASE_DIR / "servers").resolve()

REPO_DIR: Final[Path] = _repo_dir

_github_enabled_env = os.getenv("GITHUB_ENABLED", "true").lower()
GITHUB_ENABLED: Final[bool] = _github_enabled_env in ("1", "true", "yes")


GIT_REMOTE: Final[str] = os.getenv("GIT_REMOTE", "origin")
GIT_BRANCH: Final[str] = os.getenv("GIT_BRANCH", "main")

GIT_AUTHOR_NAME: Final[str] = os.getenv("GIT_AUTHOR_NAME", "tgbot")
GIT_AUTHOR_EMAIL: Final[str] = os.getenv("GIT_AUTHOR_EMAIL", "tgbot@example.com")
