from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.models import Order, OrderItem
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard
from app.utils.helpers import format_order_summary
from .admin_panel import is_admin

router = Router()


@router.callback_query(F.data.startswith("ofilter_"))
async def filter_orders(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    status = callback.data.split("_")[1]
    if status == "all":
        status = None
    async with async_session() as session:
        orders = await Order.get_by_status(session, status)
    if not orders:
        await callback.message.edit_text(
            "Bu holatda buyurtmalar yo'q",
            reply_markup=AdminKeyboard.order_status_filters()
        )
        return await callback.answer()
    for order in orders:
        async with async_session() as session:
            result = await session.execute(
                select(Order).where(Order.id == order.id)
                .options(selectinload(Order.items).selectinload(OrderItem.product))
            )
            full_order = result.scalar_one()
            text = format_order_summary(full_order, full_order.items)
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboard.order_actions(order.id, order.status)
        )
    status_labels = {
        "pending": "🕐 Kutilayotgan",
        "confirmed": "✅ Tasdiqlangan",
        "preparing": "👨‍🍳 Tayyorlanmoqda",
        "delivered": "🚚 Yetkazilgan",
        "cancelled": "❌ Bekor qilingan",
    }
    title = status_labels.get(status, "📋 Hammasi") if status else "📋 Hammasi"
    await callback.message.edit_text(
        f"{title} buyurtmalar yuqorida ko'rsatildi.",
        reply_markup=AdminKeyboard.order_status_filters()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ostatus_"))
async def change_order_status(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    _, _, order_id, new_status = callback.data.split("_", 3)
    order_id = int(order_id)
    async with async_session() as session:
        order = await Order.get(session, order_id)
        if order:
            await order.update_status(session, new_status)
    status_labels = {
        "pending": "🕐 Kutilmoqda",
        "confirmed": "✅ Tasdiqlandi",
        "preparing": "👨‍🍳 Tayyorlanmoqda",
        "delivered": "🚚 Yetkazildi",
        "cancelled": "❌ Bekor qilindi",
    }
    await callback.message.edit_text(
        f"{callback.message.text}\n\n📌 Yangi holat: {status_labels.get(new_status, new_status)}",
        reply_markup=AdminKeyboard.order_actions(order_id, new_status)
    )
    await callback.answer(f"Holat o'zgartirildi: {status_labels.get(new_status, new_status)}")
