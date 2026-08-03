from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import date
from sqlalchemy import select, func
from app.database.models import Order, OrderItem, Product, Expense
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard
from app.utils.helpers import format_currency, get_week_range, get_month_range
from .admin_panel import is_admin
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router()


class FinanceState(StatesGroup):
    description = State()
    amount = State()


async def _get_stats(callback: CallbackQuery, start_date: date, end_date: date, title: str):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        orders = await Order.get_sales_by_period(session, start_date, end_date)
        expenses = await Expense.get_by_period(session, start_date, end_date)
    total_revenue = sum(o.total_amount for o in orders)
    total_expenses = sum(e.amount for e in expenses if e.expense_type == "chiqim")
    total_income = sum(e.amount for e in expenses if e.expense_type == "kirim")
    net = total_revenue + total_income - total_expenses
    order_count = len(orders)
    text = (
        f"📊 <b>{title}</b>\n"
        f"📅 {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"
        f"📦 Buyurtmalar: {order_count} ta\n"
        f"💰 Daromad: {format_currency(total_revenue)}\n"
        f"➖ Xarajat: {format_currency(total_expenses)}\n"
        f"➕ Qo'shimcha kirim: {format_currency(total_income)}\n"
        f"═══════════════════\n"
        f"💵 <b>Sof foyda: {format_currency(net)}</b>"
    )
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.stats_menu())
    await callback.answer()


@router.callback_query(F.data == "stats_daily")
async def stats_daily(callback: CallbackQuery):
    today = date.today()
    await _get_stats(callback, today, today, "Kunlik statistika")


@router.callback_query(F.data == "stats_weekly")
async def stats_weekly(callback: CallbackQuery):
    start, end = get_week_range()
    await _get_stats(callback, start, end, "Haftalik statistika")


@router.callback_query(F.data == "stats_monthly")
async def stats_monthly(callback: CallbackQuery):
    start, end = get_month_range()
    await _get_stats(callback, start, end, "Oylik statistika")


async def show_product_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        result = await session.execute(
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
        )
        stats = result.all()
    if not stats:
        await callback.message.edit_text("Hali sotuvlar mavjud emas", reply_markup=AdminKeyboard.back())
        return await callback.answer()
    text = "<b>📈 Mahsulot sotuvlari</b>\n\n"
    for name, qty, sales in stats:
        text += f"\u2022 {name}\n  Sotilgan: {qty} dona | Summa: {format_currency(sales)}\n\n"
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.back())
    await callback.answer()


@router.callback_query(F.data == "finance_report")
async def finance_report(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        expenses = await Expense.get_all(session)
    if not expenses:
        await callback.message.edit_text("Hali xarajatlar kiritilmagan", reply_markup=AdminKeyboard.back())
        return await callback.answer()
    text = "<b>💰 Daromad / Xarajat hisoboti</b>\n\n"
    total_income = 0
    total_expense = 0
    for e in expenses:
        sign = "➕" if e.expense_type == "kirim" else "➖"
        text += f"{sign} {e.description}: {format_currency(e.amount)} ({e.date})\n"
        if e.expense_type == "kirim":
            total_income += e.amount
        else:
            total_expense += e.amount
    text += f"\n═══════════════════\n"
    text += f"➕ Jami kirim: {format_currency(total_income)}\n"
    text += f"➖ Jami chiqim: {format_currency(total_expense)}\n"
    text += f"💵 <b>Balans: {format_currency(total_income - total_expense)}</b>"
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.back())
    await callback.answer()


@router.callback_query(F.data == "finance_income")
async def finance_income_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await state.update_data(expense_type="kirim")
    await state.set_state(FinanceState.description)
    await callback.message.edit_text("Kirim uchun tavsif kiriting:")
    await callback.answer()


@router.callback_query(F.data == "finance_expense")
async def finance_expense_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await state.update_data(expense_type="chiqim")
    await state.set_state(FinanceState.description)
    await callback.message.edit_text("Chiqim uchun tavsif kiriting:")
    await callback.answer()


@router.message(FinanceState.description)
async def finance_desc(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("Tavsif juda uzun, qisqaroq kiriting:")
        return
    await state.update_data(description=message.text)
    await state.set_state(FinanceState.amount)
    await message.answer("Summani kiriting (so'mda, faqat raqam):")


@router.message(FinanceState.amount)
async def finance_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(" ", ""))
    except ValueError:
        await message.answer("Noto'g'ri summa, faqat raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        await Expense.add(session, description=data["description"], amount=amount, expense_type=data["expense_type"])
    label = "Kirim" if data["expense_type"] == "kirim" else "Chiqim"
    await message.answer(f"✅ {label} qo'shildi: {format_currency(amount)}\nTavsif: {data['description']}")
    await state.clear()
