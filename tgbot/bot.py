import asyncio
import logging
from aiogram import Bot, Dispatcher
from tgbot.config import BOT_TOKEN
from tgbot.handlers import router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await dp.start_polling(bot)  # pyright: ignore[reportUnknownMemberType]



if __name__ == "__main__":
    asyncio.run(main())
