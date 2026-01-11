import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database import AsyncSessionLocal
from app.models import GlobalSetting
from app.telegram.auth.admin import is_admin

router = Router()
logger = logging.getLogger(__name__)

class ContentSettingsState(StatesGroup):
    editing_key = State() # Ожидание ввода текста для ключа

# --- Меню редактора контента ---

@router.callback_query(F.data == "admin:settings:content")
async def content_menu(callback: CallbackQuery):
    """Меню общих текстов"""
    if not is_admin(callback.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        # Получаем текущие значения
        coords = await session.get(GlobalSetting, "coords")
        rules = await session.get(GlobalSetting, "rules")
        bath = await session.get(GlobalSetting, "bath_info")
        
    text = (
        "📝 <b>Редактор общего контента</b>\n\n"
        "Эти данные отображаются для всех гостей, независимо от домика.\n\n"
        f"📍 <b>Координаты:</b>\n{coords.value if coords else 'Не задано'}\n\n"
        f"ℹ️ <b>Общие правила:</b>\n{rules.value[:50] + '...' if rules and rules.value else 'Не задано'}\n\n"
        f"🧖‍♂️ <b>Баня/Чан:</b>\n{bath.value[:50] + '...' if bath and bath.value else 'Не задано'}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Изм. Координаты", callback_data="content:edit:coords")],
        [InlineKeyboardButton(text="ℹ️ Изм. Правила", callback_data="content:edit:rules")],
        [InlineKeyboardButton(text="🧖‍♂️ Изм. Баня/Чан", callback_data="content:edit:bath_info")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:settings")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# --- Редактирование ---

@router.callback_query(F.data.startswith("content:edit:"))
async def start_edit_content(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[2]
    
    key_names = {
        "coords": "координаты (для навигатора)",
        "rules": "общие правила проживания",
        "bath_info": "информацию о бане и чане",
    }
    
    await state.update_data(editing_key=key)
    await state.set_state(ContentSettingsState.editing_key)
    
    await callback.message.answer(
        f"✍️ Введите новые {key_names.get(key, 'данные')}:\n"
        "(Отправьте текст, можно в несколько строк)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="content:cancel")]])
    )
    await callback.answer()

@router.callback_query(F.data == "content:cancel")
async def cancel_content_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")

@router.message(ContentSettingsState.editing_key)
async def process_content_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data['editing_key']
    new_value = message.text
    
    async with AsyncSessionLocal() as session:
        setting = await session.get(GlobalSetting, key)
        if not setting:
            setting = GlobalSetting(key=key)
            session.add(setting)
        
        setting.value = new_value
        await session.commit()
            
    await state.clear()
    await message.answer(f"✅ Данные сохранены!")
    
    # Возвращаемся в меню (нужно отправить новое сообщение с кнопками)
    # Или просто кнопку "Назад в меню редактора"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В редактор", callback_data="admin:settings:content")]
    ])
    await message.answer("Вернуться к редактированию:", reply_markup=kb)
