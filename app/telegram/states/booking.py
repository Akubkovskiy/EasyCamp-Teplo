"""
FSM состояния для управления бронированием
"""
from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    waiting_for_house = State()      # Ожидание выбора домика
    waiting_for_check_in = State()   # Ожидание даты заезда (календарь)
    waiting_for_check_out = State()  # Ожидание даты выезда (календарь)
    waiting_for_guest_name = State() # Ожидание имени гостя
    waiting_for_guest_phone = State() # Ожидание телефона
    waiting_for_guests_count = State() # Ожидание количества гостей
    waiting_for_price = State()      # Ожидание цены (если ручной ввод)
    waiting_for_confirmation = State() # Ожидание подтверждения
    
    # Состояния для редактирования
    editing_dates = State()
    editing_guest_name = State()
    editing_guest_phone = State()
    editing_guests_count = State()
    editing_price = State()
    editing_status = State()
