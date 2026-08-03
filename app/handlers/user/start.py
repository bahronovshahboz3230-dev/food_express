from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from app.database.models import User
from app.database.db import async_session
from app.keyboards.user_kb import UserKeyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        await User.get_or_create(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
    await message.answer(
        "👋 <b>FoodExpress Bot</b> ga xush kelibsiz!\n\n"
        "Bu yerda yarim tayyor oziq-ovqat mahsulotlariga buyurtma berishingiz mumkin.\n\n"
        "<i>Quyidagi menyudan kerakli bo'limni tanlang:</i>",
        reply_markup=UserKeyboard.main_menu(),
    )


@router.message(F.text == "📞 Kontakt")
async def cmd_contact(message: Message):
    from .contact import show_contact
    await show_contact(message)


@router.message(F.text == "📋 Buyurtmalarim")
async def cmd_my_orders(message: Message):
    from .order import my_orders
    await my_orders(message)


@router.message(F.text == "🛒 Savat")
async def cmd_cart(message: Message):
    from .cart import show_cart
    await show_cart(message)


@router.message(F.text == "🛍 Mahsulotlar")
async def cmd_products(message: Message):
    from .menu import show_categories
    await show_categories(message)
