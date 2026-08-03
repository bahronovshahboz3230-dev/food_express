from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.database.models import User, Cart
from app.database.db import async_session
from app.keyboards.user_kb import UserKeyboard
from app.utils.helpers import format_currency

router = Router()


async def show_cart(message: Message = None, callback: CallbackQuery = None):
    user_id = message.from_user.id if message else callback.from_user.id
    async with async_session() as session:
        user = await User.get(session, user_id)
        if not user:
            text = "Avval /start ni bosing"
            if message:
                return await message.answer(text)
            return await callback.message.edit_text(text)
        cart_items = await Cart.get_user_cart(session, user.id)
    if not cart_items:
        text = "🛒 <b>Savat bo'sh</b>\n\nMahsulotlarni tanlash uchun '🛍 Mahsulotlar' bo'limiga o'ting."
        if message:
            await message.answer(text, reply_markup=UserKeyboard.back())
        else:
            await callback.message.edit_text(text, reply_markup=UserKeyboard.back())
        return
    total = sum(item.product.price * item.quantity for item in cart_items)
    text = "<b>🛒 Savatim</b>\n\n"
    for item in cart_items:
        text += (
            f"\u2022 {item.product.name}\n"
            f"  {item.quantity} x {format_currency(item.product.price)} = "
            f"<b>{format_currency(item.product.price * item.quantity)}</b>\n\n"
        )
    text += f"💰 <b>Jami: {format_currency(total)}</b>"
    if message:
        await message.answer(text, reply_markup=UserKeyboard.cart_items(cart_items))
    else:
        await callback.message.edit_text(text, reply_markup=UserKeyboard.cart_items(cart_items))


@router.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        await Cart.remove(session, cart_id)
    await callback.answer("❌ Mahsulot savatdan o'chirildi")
    await show_cart(callback=callback)


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    async with async_session() as session:
        user = await User.get(session, callback.from_user.id)
        if user:
            await Cart.clear_user_cart(session, user.id)
    await callback.answer("🔄 Savat tozalandi")
    await show_cart(callback=callback)


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("👋 Bosh menyu", reply_markup=UserKeyboard.main_menu())
