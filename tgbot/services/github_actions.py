import asyncio
import logging
from typing import Any, Optional

import aiohttp
from aiogram.types import Message

from tgbot.config import (
    GITHUB_ENABLED,
    GITHUB_TOKEN,
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_BRANCH,
)

logger = logging.getLogger("tgbot.services.github_actions")

API = "https://api.github.com"


def _headers() -> dict[str, str]:
    assert GITHUB_TOKEN is not None
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _get_json(url: str, params: Optional[dict[str, str]] = None) -> dict[str, Any]:
    async with aiohttp.ClientSession(headers=_headers()) as s:
        async with s.get(url, params=params) as r:
            if r.status >= 400:
                text = await r.text()
                raise RuntimeError(f"GitHub API {r.status}: {text}")
            return await r.json()


async def find_run_by_sha(sha: str, branch: str, attempts: int = 30) -> dict[str, Any]:
    assert GITHUB_OWNER is not None and GITHUB_REPO is not None
    url = f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs"

    for _ in range(attempts):
        data = await _get_json(url, params={"branch": branch, "event": "push", "per_page": "20"})
        for run in data.get("workflow_runs", []):
            if run.get("head_sha") == sha:
                return run
        await asyncio.sleep(2)

    raise RuntimeError("Не нашел workflow run для этого коммита (head_sha).")


async def get_run(run_id: int) -> dict[str, Any]:
    assert GITHUB_OWNER is not None and GITHUB_REPO is not None
    url = f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}"
    return await _get_json(url)


async def wait_run_completed(run_id: int, timeout_sec: int = 15 * 60) -> dict[str, Any]:
    deadline = asyncio.get_event_loop().time() + timeout_sec

    while True:
        run = await get_run(run_id)
        if run.get("status") == "completed":
            return run

        if asyncio.get_event_loop().time() > deadline:
            raise RuntimeError("Таймаут ожидания завершения workflow run.")

        await asyncio.sleep(5)


async def notify_pipeline(message: Message, sha: str) -> None:

    if not GITHUB_ENABLED:
        return

    try:
        run = await find_run_by_sha(sha=sha, branch=GITHUB_BRANCH)
        run_id = int(run["id"])

        final_run = await wait_run_completed(run_id)
        conclusion = final_run.get("conclusion")
        html_url = final_run.get("html_url")

        if conclusion == "success":
            await message.answer("✅ Пайплайн завершился успешно - конфиг должен быть рабочим.")
        else:
            await message.answer(f"❌ Пайплайн завершился с ошибкои: conclusion={conclusion}.")

        if html_url:
            await message.answer(str(html_url))

    except Exception as e:
        logger.exception("pipeline check failed sha=%s", sha)
        await message.answer(f"⚠️ Не смог проверить пайплайн: {e}")
