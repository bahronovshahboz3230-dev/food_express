from datetime import datetime, timedelta, date


def format_currency(amount: float) -> str:
    return f"{amount:,.0f} so'm"


def format_order_summary(order, items: list) -> str:
    text = f"🆔 Buyurtma #{order.id}\n"
    text += f"📅 Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"👤 Mijoz: {order.customer_name}\n"
    text += f"📞 Telefon: {order.phone or '---'}\n"
    text += f"📍 Manzil: {order.delivery_address or '---'}\n"
    if order.location_link:
        text += f"🗺 Lokatsiya: {order.location_link}\n"
    text += "\n🛒 Mahsulotlar:\n"
    for item in items:
        text += f"  \u2022 {item.product.name} x {item.quantity} = {format_currency(item.price * item.quantity)}\n"
    text += f"\n💰 Jami: {format_currency(order.total_amount)}\n"
    status_labels = {
        "pending": "🕐 Kutilmoqda",
        "confirmed": "✅ Tasdiqlandi",
        "preparing": "👨‍🍳 Tayyorlanmoqda",
        "delivered": "🚚 Yetkazildi",
        "cancelled": "❌ Bekor qilindi",
    }
    text += f"📌 Holat: {status_labels.get(order.status, order.status)}"
    return text


def get_week_range(ref_date: date = None) -> tuple:
    if ref_date is None:
        ref_date = date.today()
    start = ref_date - timedelta(days=ref_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_range(ref_date: date = None) -> tuple:
    if ref_date is None:
        ref_date = date.today()
    start = ref_date.replace(day=1)
    if ref_date.month == 12:
        end = ref_date.replace(year=ref_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = ref_date.replace(month=ref_date.month + 1, day=1) - timedelta(days=1)
    return start, end
