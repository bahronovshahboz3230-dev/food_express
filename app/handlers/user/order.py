from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.models import User, Cart, Order, OrderItem, Product
from app.database.db import async_session
from app.keyboards.user_kb import UserKeyboard
from app.states.order_states import OrderState
from app.utils.helpers import format_currency, format_order_summary
from app.config import settings

router = Router()


@router.message(F.text == "📋 Buyurtmalarim")
async def my_orders(message: Message):
    async with async_session() as session:
        user = await User.get(session, message.from_user.id)
        if not user:
            await message.answer("Avval /start ni bosing")
            return
        orders = await Order.get_user_orders(session, user.id)
    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q")
        return
    for order in orders:
        async with async_session() as session:
            result = await session.execute(
                select(Order).where(Order.id == order.id)
                .options(selectinload(Order.items).selectinload(OrderItem.product))
            )
            full_order = result.scalar_one()
            text = format_order_summary(full_order, full_order.items)
        await message.answer(text)


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        user = await User.get(session, callback.from_user.id)
        cart_items = await Cart.get_user_cart(session, user.id)
    if not cart_items:
        await callback.answer("Savat bo'sh", show_alert=True)
        return
    total = sum(item.product.price * item.quantity for item in cart_items)
    await state.update_data(total=total)
    await state.set_state(OrderState.name)
    await callback.message.delete()
    await callback.message.answer(
        "📝 <b>Buyurtma berish</b>\n\n1-qadam: Iltimos, ismingizni kiriting:",
        reply_markup=UserKeyboard.remove_keyboard()
    )
    await callback.answer()


@router.message(OrderState.name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("Ism juda uzun, qisqaroq kiriting:")
        return
    await state.update_data(customer_name=message.text)
    await state.set_state(OrderState.phone)
    await message.answer(
        "2-qadam: Telefon raqamingizni yuboring yoki yozib kiriting:",
        reply_markup=UserKeyboard.share_phone()
    )


@router.message(OrderState.phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text or (message.contact.phone_number if message.contact else None)
    if not phone:
        await message.answer("Iltimos, telefon raqamingizni kiriting yoki 📱 tugmasini bosing:")
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderState.address)
    await message.answer(
        "3-qadam: Yetkazib berish manzilini yozing yoki lokatsiya yuboring:",
        reply_markup=UserKeyboard.share_location()
    )


@router.message(OrderState.address, F.content_type == ContentType.LOCATION)
async def process_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    location_link = f"https://maps.google.com/?q={lat},{lon}"
    await state.update_data(delivery_address=f"{lat}, {lon}", location_link=location_link)
    await confirm_order(message, state)


@router.message(OrderState.address, F.text)
async def process_address_text(message: Message, state: FSMContext):
    await state.update_data(delivery_address=message.text, location_link=None)
    await confirm_order(message, state)


async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    total = data.get("total", 0)
    text = (
        "📋 <b>Buyurtma ma'lumotlari:</b>\n\n"
        f"👤 Ism: {data['customer_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Manzil: {data.get('delivery_address', '---')}\n"
    )
    if data.get("location_link"):
        text += f"🗺 Lokatsiya: <a href='{data['location_link']}'>Xaritada ko'rish</a>\n"
    text += f"\n💰 Jami: {format_currency(total)}"
    text += "\n\n<b>Tasdiqlaysizmi?</b>"
    await state.set_state(OrderState.confirm)
    await message.answer(text, reply_markup=UserKeyboard.remove_keyboard())
    await message.answer(
        "Tasdiqlash uchun tugmalardan foydalaning:",
        reply_markup=UserKeyboard.confirm_order()
    )


@router.callback_query(F.data == "confirm_order")
async def confirm_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        user = await User.get(session, callback.from_user.id)
        cart_items = await Cart.get_user_cart(session, user.id)
        if not cart_items:
            await callback.answer("Savat bo'sh", show_alert=True)
            await state.clear()
            return
        order = await Order.create(
            session, user.id,
            total_amount=data["total"],
            customer_name=data["customer_name"],
            phone=data["phone"],
            delivery_address=data.get("delivery_address"),
            location_link=data.get("location_link"),
        )
        order_items = []
        for ci in cart_items:
            order_items.append(OrderItem(
                order_id=order.id,
                product_id=ci.product_id,
                quantity=ci.quantity,
                price=ci.product.price,
            ))
        await OrderItem.bulk_create(session, order_items)
        await Cart.clear_user_cart(session, user.id)
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"Buyurtma raqami: #{order.id}\n"
        f"Jami summa: {format_currency(data['total'])}\n\n"
        f"Tez orada admin bilan bog'lanamiz.",
        reply_markup=UserKeyboard.main_menu()
    )
    texts = []
    for item in order_items:
        async with async_session() as s:
            result = await s.execute(select(Product).where(Product.id == item.product_id))
            p = result.scalar_one()
            texts.append(f"  \u2022 {p.name} x {item.quantity} = {format_currency(item.price * item.quantity)}")
    admin_text = (
        f"🆕 <b>Yangi buyurtma!</b>\n\n"
        f"🆔 #{order.id}\n"
        f"👤 {data['customer_name']}\n"
        f"📞 {data['phone']}\n"
        f"📍 {data.get('delivery_address', '---')}\n"
        f"\n🛒 Mahsulotlar:\n" + "\n".join(texts) +
        f"\n\n💰 Jami: {format_currency(data['total'])}"
    )
    try:
        await callback.bot.send_message(settings.ADMIN_ID, admin_text)
    except Exception:
        pass
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Buyurtma bekor qilindi.", reply_markup=UserKeyboard.main_menu())
    await callback.answer()
