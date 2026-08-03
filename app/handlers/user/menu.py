from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from app.database.models import Category, Product, Cart, User
from app.database.db import async_session
from app.keyboards.user_kb import UserKeyboard

router = Router()


async def show_categories(message: Message = None, callback: CallbackQuery = None):
    async with async_session() as session:
        categories = await Category.get_all(session)
    text = "📂 <b>Kategoriyalar</b>\n\nQuyidagilardan birini tanlang:"
    kb = UserKeyboard.categories(categories)
    if message:
        await message.answer(text, reply_markup=kb)
    elif callback:
        await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        category = await Category.get(session, cat_id)
        products = await Product.get_by_category(session, cat_id)
    if not products:
        await callback.answer("Bu kategoriyada mahsulot yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        f"📂 <b>{category.emoji} {category.name}</b>\n\nMahsulotlardan birini tanlang:",
        reply_markup=UserKeyboard.back_to_categories()
    )
    for product in products:
        async with async_session() as session:
            user = await User.get(session, callback.from_user.id)
            cart_qty = 0
            if user:
                result = await session.execute(
                    select(Cart).where(Cart.user_id == user.id, Cart.product_id == product.id)
                )
                cart_item = result.scalar_one_or_none()
                if cart_item:
                    cart_qty = cart_item.quantity
        text = (
            f"<b>{product.name}</b>\n"
            f"{product.description or ''}\n"
            f"💰 Narxi: <b>{product.price:,.0f} so'm</b>"
        )
        await callback.message.answer(
            text,
            reply_markup=UserKeyboard.product_controls(product.id, cart_qty)
        )
    await callback.answer()


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        categories = await Category.get_all(session)
    await callback.message.edit_text(
        "📂 <b>Kategoriyalar</b>\n\nQuyidagilardan birini tanlang:",
        reply_markup=UserKeyboard.categories(categories)
    )


@router.callback_query(F.data == "back_products")
async def back_to_products(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        categories = await Category.get_all(session)
    await callback.message.edit_text(
        "📂 <b>Kategoriyalar</b>\n\nQuyidagilardan birini tanlang:",
        reply_markup=UserKeyboard.categories(categories)
    )


@router.callback_query(F.data.startswith("inc_"))
async def increase_quantity(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        user = await User.get(session, callback.from_user.id)
        if not user:
            await callback.answer("Avval /start ni bosing", show_alert=True)
            return
        cart_item = await Cart.add_or_update(session, user.id, product_id, 1)
        qty = cart_item.quantity
    await callback.message.edit_reply_markup(
        reply_markup=UserKeyboard.product_controls(product_id, qty)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dec_"))
async def decrease_quantity(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        user = await User.get(session, callback.from_user.id)
        if not user:
            await callback.answer("Avval /start ni bosing", show_alert=True)
            return
        result = await session.execute(
            select(Cart).where(Cart.user_id == user.id, Cart.product_id == product_id)
        )
        cart_item = result.scalar_one_or_none()
        if cart_item:
            if cart_item.quantity <= 1:
                await Cart.remove(session, cart_item.id)
                qty = 0
            else:
                cart_item.quantity -= 1
                await session.commit()
                qty = cart_item.quantity
        else:
            qty = 0
    await callback.message.edit_reply_markup(
        reply_markup=UserKeyboard.product_controls(product_id, qty)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()
