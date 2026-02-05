from aiogram.fsm.state import State, StatesGroup


class CreateConfig(StatesGroup):
    waiting_for_name = State()
