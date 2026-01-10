from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def guest_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню для гостя"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Выбрать даты заезда", callback_data="guest:availability")],
        # [InlineKeyboardButton(text="ℹ️ О нас", callback_data="guest:about")], # В будущем
        # [InlineKeyboardButton(text="📞 Контакты", callback_data="guest:contacts")], # В будущем
    ])
