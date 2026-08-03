import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import settings
from app.database.db import init_db
from app.database.models import seed_data

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    from app.handlers.user.start import router as user_start_router
    from app.handlers.user.menu import router as user_menu_router
    from app.handlers.user.cart import router as user_cart_router
    from app.handlers.user.order import router as user_order_router
    from app.handlers.user.contact import router as user_contact_router
    from app.handlers.admin.admin_panel import router as admin_panel_router
    from app.handlers.admin.orders import router as admin_orders_router
    from app.handlers.admin.statistics import router as admin_statistics_router
    from app.handlers.admin.products import router as admin_products_router
    from app.handlers.admin.dashboard import router as admin_dashboard_router
    from app.handlers.admin.admin_management import router as admin_management_router

    dp.include_routers(
        user_start_router,
        user_menu_router,
        user_cart_router,
        user_order_router,
        user_contact_router,
        admin_panel_router,
        admin_orders_router,
        admin_statistics_router,
        admin_products_router,
        admin_dashboard_router,
        admin_management_router,
    )

    await init_db()
    await seed_data()

    logging.info("Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
