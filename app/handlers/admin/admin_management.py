from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database.models import Admin
from app.database.db import async_session
from app.keyboards.admin_kb import AdminKeyboard
from .admin_panel import is_admin

router = Router()


class AdminState(StatesGroup):
    waiting_id = State()


@router.callback_query(F.data == "admin_manage")
async def admin_manage_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        admins = await Admin.get_all(session)
    text = "<b>👮 Adminlarni boshqarish</b>\n\n"
    text += "Mavjud adminlar:\n"
    for a in admins:
        text += f"  \u2022 ID: <code>{a.telegram_id}</code>\n"
    text += "\nYangi admin qo'shish yoki o'chirish mumkin."
    await callback.message.edit_text(text, reply_markup=AdminKeyboard.admin_manage_menu())
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    await state.update_data(action="add")
    await state.set_state(AdminState.waiting_id)
    await callback.message.edit_text("Yangi adminning Telegram ID sini yuboring:")
    await callback.answer()


@router.callback_query(F.data == "admin_remove")
async def admin_remove_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q", show_alert=True)
    async with async_session() as session:
        admins = await Admin.get_all(session)
    text = "<b>❌ Admin o'chirish</b>\n\n"
    for a in admins:
        text += f"  \u2022 <code>{a.telegram_id}</code>\n"
    text += "\nO'chirish uchun admin ID sini yuboring:"
    await state.update_data(action="remove")
    await state.set_state(AdminState.waiting_id)
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(AdminState.waiting_id)
async def admin_handle_id(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        tg_id = int(message.text.strip())
    except ValueError:
        await message.answer("Noto'g'ri ID. Faqat raqam kiriting:")
        return
    data = await state.get_data()
    action = data.get("action")
    async with async_session() as session:
        if action == "add":
            ok = await Admin.add_admin(session, tg_id)
            if ok:
                await message.answer(f"✅ Admin qo'shildi: <code>{tg_id}</code>")
            else:
                await message.answer(f"Bu admin (<code>{tg_id}</code>) allaqachon mavjud.")
        elif action == "remove":
            ok = await Admin.remove_admin(session, tg_id)
            if ok:
                await message.answer(f"✅ Admin o'chirildi: <code>{tg_id}</code>")
            else:
                await message.answer(f"Bunday admin topilmadi.")
    await state.clear()
