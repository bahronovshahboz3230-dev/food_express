from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    name = State()
    phone = State()
    address = State()
    location = State()
    confirm = State()
