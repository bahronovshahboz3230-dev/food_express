from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from app.config import settings
from app.database.models import Admin
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard

router = Router()


async def is_admin(user_id: int) -> bool:
    if user_id == settings.ADMIN_ID:
        return True
    async with async_session() as session:
        return await Admin.is_admin(session, user_id)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz")
        return
    await message.answer(
        "👨‍💼 <b>Admin panel</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=AdminKeyboard.main_menu()
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "👨‍💼 <b>Admin panel</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=AdminKeyboard.main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "📦 <b>Buyurtmalar</b>\n\nHolatni tanlang:",
        reply_markup=AdminKeyboard.order_status_filters()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "📊 <b>Statistika</b>\n\nDavrni tanlang:",
        reply_markup=AdminKeyboard.stats_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_finance")
async def admin_finance_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "💰 <b>Daromad / Xarajat</b>\n\nAmalni tanlang:",
        reply_markup=AdminKeyboard.finance_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_product_stats")
async def admin_product_stats_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    from .statistics import show_product_stats
    await show_product_stats(callback)


@router.callback_query(F.data == "admin_products")
async def admin_products_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "✏️ <b>Mahsulotlarni boshqarish</b>\n\nAmalni tanlang:",
        reply_markup=AdminKeyboard.product_menu()
    )
    await callback.answer()
