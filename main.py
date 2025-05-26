# Import assert
import asyncio


# Import Libary aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from src.utils.logging import write_logs

# Import all libary
from src.config.config import settings
from src.utils.localization import init_default_messages

from src.handlers.common import router as common_router
from src.handlers.callback import router as callback_router
from src.handlers.survey_questions.survey import router as survey_router
from src.handlers.admin import router as admin_router

# from handlers.callback import router as callback_router
from src.database.settings_data import init_db

# Enable logging


async def routers(dp, bot):
    routers = [
        common_router,
        survey_router,
        callback_router,
        admin_router,
    ]

    for router in routers:
        dp.include_router(router)
    await dp.start_polling(bot)


# Start main
async def main() -> None:

    await init_db()
    await init_default_messages()  # Initialize localization messages

    try:
        bot = Bot(
            token=settings.config.bot_token,
            # default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )
        dp = Dispatcher(storage=MemoryStorage())
        await bot.delete_webhook(drop_pending_updates=True)

        await write_logs("info", f"Bot is ready to work")

        # start routers
        await routers(dp, bot)
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as Error:
        asyncio.run(write_logs("error", f"Bot work off.. {Error}"))
