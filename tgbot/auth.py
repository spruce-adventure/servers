import json
from tgbot.config import WHITELIST_PATH


def is_allowed(user_id: int) -> bool:
    if not WHITELIST_PATH.exists():
        return False

    with open(WHITELIST_PATH) as f:
        data = json.load(f)

    return user_id in data.get("allowed_users", [])
