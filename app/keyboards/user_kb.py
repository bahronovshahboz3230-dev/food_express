from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UserKeyboard:

    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🛍 Mahsulotlar")],
                [KeyboardButton(text="🛒 Savat"), KeyboardButton(text="📋 Buyurtmalarim")],
                [KeyboardButton(text="📞 Kontakt")],
            ],
            resize_keyboard=True
        )

    @staticmethod
    def categories(categories: list):
        builder = InlineKeyboardBuilder()
        for cat in categories:
            builder.button(text=f"{cat.emoji} {cat.name}", callback_data=f"cat_{cat.id}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def back_to_categories():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_categories")]
            ]
        )

    @staticmethod
    def product_controls(product_id: int, cart_quantity: int = 0):
        btns = []
        if cart_quantity > 0:
            btns.append([
                InlineKeyboardButton(text="➖", callback_data=f"dec_{product_id}"),
                InlineKeyboardButton(text=f"{cart_quantity}", callback_data="noop"),
                InlineKeyboardButton(text="➕", callback_data=f"inc_{product_id}"),
            ])
        else:
            btns.append([
                InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"inc_{product_id}"),
            ])
        btns.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_products")])
        return InlineKeyboardMarkup(inline_keyboard=btns)

    @staticmethod
    def cart_items(cart_items: list):
        builder = InlineKeyboardBuilder()
        for item in cart_items:
            builder.button(
                text=f"❌ {item.product.name} ({item.quantity} dona)",
                callback_data=f"remove_cart_{item.id}"
            )
        builder.adjust(1)
        builder.row(InlineKeyboardButton(text="🔄 Tozalash", callback_data="clear_cart"))
        builder.row(InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout"))
        builder.row(InlineKeyboardButton(text="⬅️ Menu", callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def share_phone():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            ],
            resize_keyboard=True, one_time_keyboard=True
        )

    @staticmethod
    def share_location():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True)],
                [KeyboardButton(text="✍️ Manzilni yozish")],
            ],
            resize_keyboard=True, one_time_keyboard=True
        )

    @staticmethod
    def confirm_order():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")],
            ]
        )

    @staticmethod
    def contact():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📞 Admin bilan bog'lanish", url="https://t.me/foodexpress_admin")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_main")],
            ]
        )

    @staticmethod
    def back():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_main")],
            ]
        )

    @staticmethod
    def remove_keyboard():
        from aiogram.types import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
