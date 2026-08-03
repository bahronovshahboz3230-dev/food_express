from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database.models import Category, Product
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard
from app.utils.helpers import format_currency
from .admin_panel import is_admin

router = Router()


class ProductState(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    photo = State()


@router.callback_query(F.data == "prod_add")
async def prod_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        categories = await Category.get_all(session)
    text = "Kategoriyani tanlang:\n" + "\n".join(
        [f"{c.emoji} {c.name} (id: {c.id})" for c in categories]
    )
    await state.set_state(ProductState.category)
    await callback.message.edit_text(text + "\n\nKategoriya ID sini kiriting:")
    await callback.answer()


@router.message(ProductState.category)
async def prod_category(message: Message, state: FSMContext):
    try:
        cat_id = int(message.text)
    except ValueError:
        await message.answer("ID raqam bo'lishi kerak:")
        return
    async with async_session() as session:
        cat = await Category.get(session, cat_id)
        if not cat:
            await message.answer("Bunday kategoriya yo'q, qaytadan kiriting:")
            return
    await state.update_data(category_id=cat_id)
    await state.set_state(ProductState.name)
    await message.answer("Mahsulot nomini kiriting:")


@router.message(ProductState.name)
async def prod_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProductState.description)
    await message.answer("Mahsulot tavsifini kiriting (yoki '/' tashlab o'ting):")


@router.message(ProductState.description)
async def prod_description(message: Message, state: FSMContext):
    desc = None if message.text == "/" else message.text
    await state.update_data(description=desc)
    await state.set_state(ProductState.price)
    await message.answer("Narxni kiriting (so'mda, faqat raqam):")


@router.message(ProductState.price)
async def prod_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(" ", ""))
    except ValueError:
        await message.answer("Noto'g'ri narx, faqat raqam:")
        return
    await state.update_data(price=price)
    await state.set_state(ProductState.photo)
    await message.answer("Mahsulot rasmini yuboring (yoki '/' tashlab o'ting):")


@router.message(ProductState.photo)
async def prod_photo(message: Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text == "/":
        photo_id = None
    else:
        await message.answer("Rasm yuboring yoki '/' yozing:")
        return
    data = await state.get_data()
    async with async_session() as session:
        prod = Product(
            category_id=data["category_id"], name=data["name"],
            description=data.get("description"), price=data["price"], photo_id=photo_id,
        )
        session.add(prod)
        await session.commit()
    await message.answer(f"✅ Mahsulot qo'shildi:\n{data['name']} - {format_currency(data['price'])}")
    await state.clear()


@router.callback_query(F.data == "prod_remove")
async def prod_remove_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        products = await Product.get_all(session)
    if not products:
        await callback.message.edit_text("Mahsulotlar yo'q", reply_markup=AdminKeyboard.back())
        return await callback.answer()
    text = "<b>Mahsulot o'chirish</b>\n\n"
    for p in products:
        text += f"ID {p.id}: {p.name} - {format_currency(p.price)}\n"
    text += "\nO'chirish uchun mahsulot ID sini yuboring:"
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.back())
    await callback.answer()


@router.message(F.text.regexp(r"^\d+$"))
async def prod_remove_execute(message: Message):
    if not await is_admin(message.from_user.id):
        return
    prod_id = int(message.text)
    async with async_session() as session:
        prod = await Product.get(session, prod_id)
        if not prod:
            await message.answer("Bunday mahsulot yo'q")
            return
        prod.is_available = False
        await session.commit()
    await message.answer("✅ Mahsulot o'chirildi")


@router.callback_query(F.data == "prod_list")
async def prod_list(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        products = await Product.get_all(session)
    if not products:
        await callback.message.edit_text("Mahsulotlar yo'q", reply_markup=AdminKeyboard.back())
        return await callback.answer()
    text = "<b>📋 Mahsulotlar ro'yxati</b>\n\n"
    for p in products:
        async with async_session() as s:
            cat = await Category.get(s, p.category_id)
        text += f"\u2022 {cat.emoji if cat else ''} {p.name}\n  💰 {format_currency(p.price)}\n"
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.back())
    await callback.answer()
