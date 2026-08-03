from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.keyboards.user_kb import UserKeyboard

router = Router()


async def show_contact(message: Message = None, callback: CallbackQuery = None):
    text = (
        "📞 <b>Biz bilan bog'lanish</b>\n\n"
        "Savol va takliflaringiz bo'lsa, admin bilan bog'lanishingiz mumkin.\n\n"
        "📱 Telefon: +998 XX XXX XX XX\n"
        "🌐 Instagram: @foodexpress\n"
        "📧 Email: info@foodexpress.uz"
    )
    if message:
        await message.answer(text, reply_markup=UserKeyboard.contact())
    elif callback:
        await callback.message.edit_text(text, reply_markup=UserKeyboard.contact())
        await callback.answer()
