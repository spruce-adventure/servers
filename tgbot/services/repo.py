import logging
import os
import subprocess
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

from tgbot.config import (
    REPO_DIR,
    GIT_REMOTE,
    GIT_BRANCH,
    GIT_AUTHOR_NAME,
    GIT_AUTHOR_EMAIL,
)

logger = logging.getLogger("tgbot.services.repo")

WIREGUARD_CLIENTS = REPO_DIR / "wireguard-clients.yml"
NEW_CLIENT_SCRIPT = REPO_DIR / "new-client"
LOCK_DIR = REPO_DIR / ".tgbot.lock"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _run_checked(cmd: list[str], cwd: Path, err_hint: str) -> str:
    p = _run(cmd, cwd)
    if p.returncode != 0:
        msg = (p.stderr or p.stdout or err_hint).strip()
        raise RuntimeError(msg)
    return p.stdout


class RepoLock:
    def __enter__(self) -> None:
        try:
            LOCK_DIR.mkdir(exist_ok=False)
        except FileExistsError:
            raise RuntimeError("Сейчас уже идет создание конфига. Попробуй еще раз через минуту.")


    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        try:
            LOCK_DIR.rmdir()
        except Exception:
            pass



def client_exists(name: str) -> bool:
    if not WIREGUARD_CLIENTS.exists():
        raise RuntimeError(f"Не найден {WIREGUARD_CLIENTS}")

    p = _run(["grep", "-q", f"^{name}:", str(WIREGUARD_CLIENTS)], REPO_DIR)
    return p.returncode == 0


def run_new_client(name: str) -> str:
    if not NEW_CLIENT_SCRIPT.exists():
        raise RuntimeError(f"Не найден скрипт {NEW_CLIENT_SCRIPT}")
    p = _run([str(NEW_CLIENT_SCRIPT), name], REPO_DIR)

    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "new-client failed").strip())

    if not p.stdout.strip():
        raise RuntimeError("new-client вернул пустой stdout (ожидался конфиг)")

    return p.stdout


def git_has_changes() -> bool:
    out = _run_checked(["git", "status", "--porcelain"], REPO_DIR, "git status failed")
    return bool(out.strip())


def git_commit_and_push(client_name: str, user_id: int) -> str:
    logger.info("git add/commit/push for client=%s tg=%s", client_name, user_id)

    _run_checked(["git", "add", "-A"], REPO_DIR, "git add failed")

    env: dict[str, str] = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = GIT_AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = GIT_AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = GIT_AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = GIT_AUTHOR_EMAIL

    msg = f"wireguard: add client {client_name} (tg {user_id})"
    p = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=str(REPO_DIR),
        capture_output=True,
        text=True,
        env=env,
    )
    if p.returncode != 0:
        out = (p.stderr or p.stdout or "").strip().lower()
        if "nothing to commit" not in out:
            raise RuntimeError((p.stderr or p.stdout or "git commit failed").strip())

    _run_checked(["git", "pull", "--rebase", GIT_REMOTE, GIT_BRANCH], REPO_DIR, "git pull --rebase failed")
    _run_checked(["git", "push", GIT_REMOTE, GIT_BRANCH], REPO_DIR, "git push failed")

    sha = _run_checked(["git", "rev-parse", "HEAD"], REPO_DIR, "git rev-parse failed").strip()
    logger.info("pushed sha=%s", sha)
    return sha
