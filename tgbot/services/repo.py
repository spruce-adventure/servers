import asyncio
import logging
import os
import subprocess
from pathlib import Path



repo_lock = asyncio.Lock()


from tgbot.config import (
    REPO_DIR,
    GIT_REMOTE,
    GIT_BRANCH,
    GIT_AUTHOR_NAME,
    GIT_AUTHOR_EMAIL,
)

logger = logging.getLogger("tgbot.services.repo")

NEW_CLIENT_SCRIPT = REPO_DIR / "new-client"
LOCK_DIR = REPO_DIR / ".tgbot.lock"


def _run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )


def _run_checked(
    cmd: list[str],
    cwd: Path,
    err_hint: str,
    env: dict[str, str] | None = None,
) -> str:
    p = _run(cmd, cwd, env=env)

    if p.returncode != 0:
        msg = (p.stderr or p.stdout or err_hint).strip()
        raise RuntimeError(msg)

    return p.stdout




def run_new_client(name: str) -> str:
    if not NEW_CLIENT_SCRIPT.exists():
        raise RuntimeError(f"Не найден скрипт {NEW_CLIENT_SCRIPT}")

    p = _run([str(NEW_CLIENT_SCRIPT), name], REPO_DIR)

    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "new-client failed").strip())

    out = p.stdout.strip()
    if not out:
        raise RuntimeError("new-client вернул пустой stdout (ожидался конфиг)")

    return out


def git_has_changes() -> bool:
    out = _run_checked(["git", "status", "--porcelain"], REPO_DIR, "git status failed")
    return bool(out.strip())


def _git_stage_expected_changes() -> None:
    _run_checked(["git", "add", "-u"], REPO_DIR, "git add -u failed")


def git_commit_and_push(client_name: str, user_id: int) -> str:
    logger.info("git add/commit/push for client=%s tg=%s", client_name, user_id)

    _git_stage_expected_changes()

    env: dict[str, str] = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = GIT_AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = GIT_AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = GIT_AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = GIT_AUTHOR_EMAIL

    msg = f"wireguard: add client {client_name} (tg {user_id})"
    p = _run(["git", "commit", "-m", msg], REPO_DIR, env=env)

    if p.returncode != 0:
        out = (p.stderr or p.stdout or "").strip().lower()
        if "nothing to commit" not in out:
            raise RuntimeError((p.stderr or p.stdout or "git commit failed").strip())

    _run_checked(["git", "pull", GIT_REMOTE, GIT_BRANCH], REPO_DIR, "git pull failed")
    _run_checked(["git", "push", GIT_REMOTE, GIT_BRANCH], REPO_DIR, "git push failed")

    sha = _run_checked(["git", "rev-parse", "HEAD"], REPO_DIR, "git rev-parse failed").strip()
    logger.info("pushed sha=%s", sha)
    return sha
