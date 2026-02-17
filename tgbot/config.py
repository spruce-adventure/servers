import os
from pathlib import Path
from typing import Final

BASE_DIR: Final = Path(os.getenv("BASE_DIR", Path.cwd()))

# Telegram
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise RuntimeError("BOT_TOKEN is not set")

WHITELIST_PATH = BASE_DIR / "whitelist.json"

# Repo (commit/push)
REPO_DIR: Final[Path] = Path(
    os.getenv("REPO_DIR", BASE_DIR / "servers")
).resolve()

if not REPO_DIR.exists():
    raise RuntimeError(f"REPO_DIR does not exist: {REPO_DIR}")


GIT_REMOTE: Final[str] = os.getenv("GIT_REMOTE", "origin")
GIT_BRANCH: Final[str] = os.getenv("GIT_BRANCH", "main")

GIT_AUTHOR_NAME: Final[str] = os.getenv("GIT_AUTHOR_NAME", "servers-bot")
GIT_AUTHOR_EMAIL: Final[str] = os.getenv("GIT_AUTHOR_EMAIL", "servers-bot@local")

# GitHub Actions
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH: Final[str] = os.getenv("GITHUB_BRANCH", "main")

GITHUB_ENABLED: Final[bool] = bool(GITHUB_TOKEN and GITHUB_OWNER and GITHUB_REPO)
