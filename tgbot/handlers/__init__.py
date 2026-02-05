from aiogram import Router

from tgbot.handlers.start import router as start_router
from tgbot.handlers.create_client import router as create_client_router

router = Router()

router.include_router(start_router)
router.include_router(create_client_router)
