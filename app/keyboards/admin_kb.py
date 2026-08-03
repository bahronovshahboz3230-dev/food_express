from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminKeyboard:

    @staticmethod
    def main_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Dashboard", callback_data="admin_dashboard")],
                [InlineKeyboardButton(text="📦 Buyurtmalar", callback_data="admin_orders")],
                [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
                [InlineKeyboardButton(text="💰 Daromad / Xarajat", callback_data="admin_finance")],
                [InlineKeyboardButton(text="📈 Mahsulot statistikasi", callback_data="admin_product_stats")],
                [InlineKeyboardButton(text="✏️ Mahsulotlar", callback_data="admin_products")],
                [InlineKeyboardButton(text="👮 Adminlar", callback_data="admin_manage")],
            ]
        )

    @staticmethod
    def admin_manage_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add")],
                [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="admin_remove")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def order_status_filters():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🕐 Kutilayotgan", callback_data="ofilter_pending")],
                [InlineKeyboardButton(text="✅ Tasdiqlangan", callback_data="ofilter_confirmed")],
                [InlineKeyboardButton(text="👨‍🍳 Tayyorlanmoqda", callback_data="ofilter_preparing")],
                [InlineKeyboardButton(text="🚚 Yetkazilgan", callback_data="ofilter_delivered")],
                [InlineKeyboardButton(text="❌ Bekor qilingan", callback_data="ofilter_cancelled")],
                [InlineKeyboardButton(text="📋 Hammasi", callback_data="ofilter_all")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def order_actions(order_id: int, current_status: str):
        btns = []
        status_flow = ["pending", "confirmed", "preparing", "delivered"]
        for s in status_flow:
            if s == current_status:
                continue
            labels = {
                "pending": "🕐 Kutilmoqda",
                "confirmed": "✅ Tasdiqlash",
                "preparing": "👨‍🍳 Tayyorlash",
                "delivered": "🚚 Yetkazildi",
            }
            btns.append([InlineKeyboardButton(text=labels.get(s, s), callback_data=f"ostatus_{order_id}_{s}")])
        btns.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"ostatus_{order_id}_cancelled")])
        btns.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_orders")])
        return InlineKeyboardMarkup(inline_keyboard=btns)

    @staticmethod
    def stats_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Kunlik", callback_data="stats_daily")],
                [InlineKeyboardButton(text="📅 Haftalik", callback_data="stats_weekly")],
                [InlineKeyboardButton(text="📅 Oylik", callback_data="stats_monthly")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def finance_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Kirim qo'shish", callback_data="finance_income")],
                [InlineKeyboardButton(text="➖ Chiqim qo'shish", callback_data="finance_expense")],
                [InlineKeyboardButton(text="📊 Hisobot", callback_data="finance_report")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def product_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yangi mahsulot", callback_data="prod_add")],
                [InlineKeyboardButton(text="❌ Mahsulot o'chirish", callback_data="prod_remove")],
                [InlineKeyboardButton(text="📋 Mahsulotlar ro'yxati", callback_data="prod_list")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def back():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back")],
            ]
        )
