from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import date
from sqlalchemy import select, func
from app.database.models import User, Order, OrderItem, Product, Expense
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard
from app.utils.helpers import format_currency, get_week_range, get_month_range
from .admin_panel import is_admin

router = Router()


@router.callback_query(F.data == "admin_dashboard")
async def show_dashboard(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)

    today = date.today()
    week_start, week_end = get_week_range()
    month_start, month_end = get_month_range()

    async with async_session() as session:
        total_users = await session.execute(select(func.count(User.id)))
        total_users = total_users.scalar()

        total_orders = await session.execute(select(func.count(Order.id)))
        total_orders = total_orders.scalar()

        today_orders = await session.execute(
            select(func.count(Order.id)).where(func.date(Order.created_at) == today)
        )
        today_orders = today_orders.scalar()

        today_revenue = await session.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                func.date(Order.created_at) == today,
                Order.status.in_(["delivered", "confirmed"])
            )
        )
        today_revenue = today_revenue.scalar()

        week_orders = await Order.get_sales_by_period(session, week_start, week_end)
        week_revenue = sum(o.total_amount for o in week_orders)

        month_orders = await Order.get_sales_by_period(session, month_start, month_end)
        month_revenue = sum(o.total_amount for o in month_orders)

        today_expenses = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.date == today,
                Expense.expense_type == "chiqim"
            )
        )
        today_expenses = today_expenses.scalar()

        top_products = await session.execute(
            select(
                Product.name,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.quantity * OrderItem.price).label("total_sales")
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status.in_(["delivered", "confirmed"]))
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )
        top_products = top_products.all()

        pending_orders = await session.execute(
            select(func.count(Order.id)).where(Order.status == "pending")
        )
        pending_orders = pending_orders.scalar()

        week_expenses_result = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.date.between(week_start, week_end),
                Expense.expense_type == "chiqim"
            )
        )
        week_expenses = week_expenses_result.scalar()

        month_expenses_result = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.date.between(month_start, month_end),
                Expense.expense_type == "chiqim"
            )
        )
        month_expenses = month_expenses_result.scalar()

    today_net = today_revenue - today_expenses

    text = (
        "🏠 <b>Admin Dashboard</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {total_users} ta\n"
        f"📦 <b>Jami buyurtmalar:</b> {total_orders} ta\n"
        f"🕐 <b>Kutilayotgan buyurtmalar:</b> {pending_orders} ta\n"
        f"\n═══════════════════\n"
        f"<b>📅 Bugun ({today.strftime('%d.%m.%Y')})</b>\n"
        f"  Buyurtmalar: {today_orders} ta\n"
        f"  Daromad: {format_currency(today_revenue)}\n"
        f"  Xarajat: {format_currency(today_expenses)}\n"
        f"  <b>Sof foyda: {format_currency(today_net)}</b>\n"
        f"\n═══════════════════\n"
        f"<b>📅 Bu hafta</b>\n"
        f"  Buyurtmalar: {len(week_orders)} ta\n"
        f"  Daromad: {format_currency(week_revenue)}\n"
        f"  Xarajat: {format_currency(week_expenses)}\n"
        f"  <b>Sof foyda: {format_currency(week_revenue - week_expenses)}</b>\n"
        f"\n═══════════════════\n"
        f"<b>📅 Bu oy</b>\n"
        f"  Buyurtmalar: {len(month_orders)} ta\n"
        f"  Daromad: {format_currency(month_revenue)}\n"
        f"  Xarajat: {format_currency(month_expenses)}\n"
        f"  <b>Sof foyda: {format_currency(month_revenue - month_expenses)}</b>\n"
    )

    if top_products:
        text += "\n═══════════════════\n<b>🏆 Top 5 mahsulotlar</b>\n"
        for i, (name, qty, sales) in enumerate(top_products, 1):
            text += f"{i}. {name} - {qty} dona ({format_currency(sales)})\n"

    await callback.message.edit_text(text, reply_markup=AdminKeyboard.main_menu())
    await callback.answer()
