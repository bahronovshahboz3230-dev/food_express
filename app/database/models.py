from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, BigInteger, Float, Boolean, Text,
    ForeignKey, DateTime, Date, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
import enum

from .db import Base, async_session


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    delivered = "delivered"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    registered_at = Column(DateTime, default=datetime.now)

    cart_items = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    @classmethod
    async def get_or_create(cls, session: AsyncSession, telegram_id: int, username: str = None, full_name: str = None):
        result = await session.execute(select(cls).where(cls.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = cls(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    @classmethod
    async def get(cls, session: AsyncSession, telegram_id: int):
        result = await session.execute(select(cls).where(cls.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @classmethod
    async def update_phone(cls, session: AsyncSession, telegram_id: int, phone: str):
        user = await cls.get(session, telegram_id)
        if user:
            user.phone = phone
            await session.commit()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    emoji = Column(String(10), default="📦")

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls).order_by(cls.id))
        return result.scalars().all()

    @classmethod
    async def get(cls, session: AsyncSession, category_id: int):
        result = await session.execute(select(cls).where(cls.id == category_id))
        return result.scalar_one_or_none()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    photo_id = Column(String(512), nullable=True)
    is_available = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    cart_items = relationship("Cart", back_populates="product", cascade="all, delete-orphan")

    @classmethod
    async def get_by_category(cls, session: AsyncSession, category_id: int):
        result = await session.execute(
            select(cls).where(cls.category_id == category_id, cls.is_available == True)
        )
        return result.scalars().all()

    @classmethod
    async def get(cls, session: AsyncSession, product_id: int):
        result = await session.execute(select(cls).where(cls.id == product_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls).where(cls.is_available == True))
        return result.scalars().all()


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product"),)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    @classmethod
    async def get_user_cart(cls, session: AsyncSession, user_id: int):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id)
            .options(selectinload(cls.product))
        )
        return result.scalars().all()

    @classmethod
    async def add_or_update(cls, session: AsyncSession, user_id: int, product_id: int, quantity: int = 1):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id, cls.product_id == product_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.quantity += quantity
        else:
            item = cls(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(item)
        await session.commit()
        return item

    @classmethod
    async def remove(cls, session: AsyncSession, cart_id: int):
        await session.execute(delete(cls).where(cls.id == cart_id))
        await session.commit()

    @classmethod
    async def clear_user_cart(cls, session: AsyncSession, user_id: int):
        await session.execute(delete(cls).where(cls.user_id == user_id))
        await session.commit()

    @classmethod
    async def update_quantity(cls, session: AsyncSession, cart_id: int, quantity: int):
        result = await session.execute(select(cls).where(cls.id == cart_id))
        item = result.scalar_one_or_none()
        if item:
            if quantity <= 0:
                await cls.remove(session, cart_id)
                return None
            item.quantity = quantity
            await session.commit()
            return item
        return None


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, default=0)
    status = Column(String(20), default=OrderStatus.pending.value)
    customer_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    delivery_address = Column(Text, nullable=True)
    location_link = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @classmethod
    async def create(cls, session: AsyncSession, user_id: int, **kwargs):
        order = cls(user_id=user_id, **kwargs)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    @classmethod
    async def get(cls, session: AsyncSession, order_id: int):
        result = await session.execute(select(cls).where(cls.id == order_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_status(cls, session: AsyncSession, status: str = None):
        query = select(cls).order_by(cls.created_at.desc())
        if status:
            query = query.where(cls.status == status)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls).order_by(cls.created_at.desc()))
        return result.scalars().all()

    async def update_status(self, session: AsyncSession, new_status: str):
        self.status = new_status
        await session.commit()

    @classmethod
    async def get_sales_by_period(cls, session: AsyncSession, start_date: date, end_date: date):
        from sqlalchemy import and_
        result = await session.execute(
            select(cls).where(
                and_(cls.created_at >= start_date, cls.created_at <= end_date,
                     cls.status.in_(["delivered", "confirmed"]))
            )
        )
        return result.scalars().all()

    @classmethod
    async def get_user_orders(cls, session: AsyncSession, user_id: int):
        result = await session.execute(
            select(cls).where(cls.user_id == user_id).order_by(cls.created_at.desc())
        )
        return result.scalars().all()


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    @classmethod
    async def bulk_create(cls, session: AsyncSession, items: list):
        session.add_all(items)
        await session.commit()


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    added_at = Column(DateTime, default=datetime.now)

    @classmethod
    async def is_admin(cls, session: AsyncSession, telegram_id: int) -> bool:
        result = await session.execute(select(cls).where(cls.telegram_id == telegram_id))
        return result.scalar_one_or_none() is not None

    @classmethod
    async def add_admin(cls, session: AsyncSession, telegram_id: int):
        exists = await cls.is_admin(session, telegram_id)
        if not exists:
            session.add(cls(telegram_id=telegram_id))
            await session.commit()
            return True
        return False

    @classmethod
    async def remove_admin(cls, session: AsyncSession, telegram_id: int):
        result = await session.execute(select(cls).where(cls.telegram_id == telegram_id))
        admin = result.scalar_one_or_none()
        if admin:
            await session.delete(admin)
            await session.commit()
            return True
        return False

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls))
        return result.scalars().all()


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    expense_type = Column(String(10), default="chiqim")
    date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.now)

    @classmethod
    async def add(cls, session: AsyncSession, **kwargs):
        expense = cls(**kwargs)
        session.add(expense)
        await session.commit()
        return expense

    @classmethod
    async def get_by_period(cls, session: AsyncSession, start_date: date, end_date: date):
        from sqlalchemy import and_
        result = await session.execute(
            select(cls).where(
                and_(cls.date >= start_date, cls.date <= end_date)
            ).order_by(cls.date.desc())
        )
        return result.scalars().all()

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls).order_by(cls.date.desc()))
        return result.scalars().all()


async def seed_data():
    from app.config import settings
    async with async_session() as session:
        await Admin.add_admin(session, settings.ADMIN_ID)

        result = await session.execute(select(Category))
        if result.scalars().first():
            return

        categories_data = [
            {"name": "Manti", "emoji": "🥟"},
            {"name": "Chuchvara", "emoji": "🥟"},
            {"name": "Golubsi", "emoji": "🥬"},
            {"name": "Kotlet", "emoji": "🥩"},
            {"name": "Dolma", "emoji": "🍇"},
            {"name": "Somsa", "emoji": "🥟"},
        ]

        products_data = [
            {"category": "Manti", "name": "Manti (5 dona)", "price": 25000, "description": "5 dona manti"},
            {"category": "Manti", "name": "Manti (10 dona)", "price": 45000, "description": "10 dona manti"},
            {"category": "Chuchvara", "name": "Chuchvara (0.5 kg)", "price": 18000, "description": "0.5 kg chuchvara"},
            {"category": "Chuchvara", "name": "Chuchvara (1 kg)", "price": 32000, "description": "1 kg chuchvara"},
            {"category": "Golubsi", "name": "Golubsi (5 dona)", "price": 30000, "description": "5 dona golubsi"},
            {"category": "Golubsi", "name": "Golubsi (10 dona)", "price": 55000, "description": "10 dona golubsi"},
            {"category": "Kotlet", "name": "Kotlet (0.5 kg)", "price": 22000, "description": "0.5 kg kotlet"},
            {"category": "Kotlet", "name": "Kotlet (1 kg)", "price": 40000, "description": "1 kg kotlet"},
            {"category": "Dolma", "name": "Dolma (10 dona)", "price": 28000, "description": "10 dona dolma"},
            {"category": "Somsa", "name": "Go'shtli somsa (5 dona)", "price": 20000, "description": "5 dona somsa"},
        ]

        categories = {}
        for cat_data in categories_data:
            cat = Category(**cat_data)
            session.add(cat)
            await session.flush()
            categories[cat.name] = cat

        for prod_data in products_data:
            cat_name = prod_data.pop("category")
            prod = Product(category_id=categories[cat_name].id, **prod_data)
            session.add(prod)

        await session.commit()
