from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.models import UserRole
from app.telegram.auth.admin import add_user, remove_user, get_all_users, is_admin

router = Router()


class UserAddStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()


@router.callback_query(F.data == "settings_users")
async def settings_users_menu(callback: CallbackQuery):
    """Меню управления пользователями"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👮‍♂️ Администраторы", callback_data="users_list:admin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Клининг (Уборщицы)", callback_data="users_list:cleaner"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:settings")],
        ]
    )

    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите категорию пользователей для настройки доступа:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("users_list:"))
async def show_users_list(callback: CallbackQuery):
    """Показать список пользователей определенной роли"""
    role_str = callback.data.split(":")[1]
    role = UserRole.ADMIN if role_str == "admin" else UserRole.CLEANER
    role_name = "Администраторы" if role == UserRole.ADMIN else "Уборщицы"

    users = await get_all_users()
    role_users = [u for u in users if u.role == role]

    # Формируем список
    text = f"👥 <b>{role_name}</b>\n\n"

    if not role_users:
        text += "<i>Список пуст</i>\n"
    else:
        for u in role_users:
            text += f"👤 <b>{u.name}</b> (ID: <code>{u.telegram_id}</code>)\n"

    # Клавиатура
    buttons = []
    # Кнопки удаления для каждого
    for u in role_users:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Удалить {u.name}",
                    callback_data=f"user_remove:{u.telegram_id}:{role_str}",
                )
            ]
        )

    # Добавить нового
    buttons.append(
        [
            InlineKeyboardButton(
                text=f"➕ Добавить {role_name[:-1].lower()}а",  # "Администратора" / "Уборщиц" (fix ending logic manually simpler)
                callback_data=f"user_add_start:{role_str}",
            )
        ]
    )

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_users")]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("user_add_start:"))
async def start_add_user(callback: CallbackQuery, state: FSMContext):
    """Начало добавления пользователя"""
    role_str = callback.data.split(":")[1]

    await state.update_data(role=role_str)
    await state.set_state(UserAddStates.waiting_for_id)

    await callback.message.edit_text(
        f"➕ <b>Добавление пользователя</b>\n\n"
        "Пожалуйста, отправьте <b>Telegram ID</b> пользователя (число) или перешлите сообщение от него.\n\n"
        "<i>Узнать ID можно через бота @userinfobot</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Отмена", callback_data=f"users_list:{role_str}"
                    )
                ]
            ]
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(UserAddStates.waiting_for_id)
async def process_user_id(message: Message, state: FSMContext):
    """Обработка ID пользователя"""
    if not message.text and not message.forward_from:
        await message.answer(
            "❌ Пожалуйста, отправьте ID числом или перешлите сообщение."
        )
        return

    user_id = None
    if message.forward_from:
        user_id = message.forward_from.id
    else:
        try:
            user_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ ID должен быть числом.")
            return

    await state.update_data(telegram_id=user_id)
    await state.set_state(UserAddStates.waiting_for_name)

    await message.answer(
        f"✅ ID получен: <code>{user_id}</code>\n\n"
        "Теперь введите <b>Имя пользователя</b> (для удобства отображения в списке):"
    )


@router.message(UserAddStates.waiting_for_name)
async def process_user_name(message: Message, state: FSMContext):
    """Обработка имени и сохранение"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите текстовое имя.")
        return

    name = message.text.strip()
    data = await state.get_data()

    telegram_id = data["telegram_id"]
    role_str = data["role"]
    role = UserRole.ADMIN if role_str == "admin" else UserRole.CLEANER
    role_name = "Администратор" if role == UserRole.ADMIN else "Уборщица"

    # Сохраняем
    success = await add_user(telegram_id, role, name)

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 К списку", callback_data=f"users_list:{role_str}"
                )
            ]
        ]
    )

    if success:
        await message.answer(
            f"✅ <b>{role_name} добавлен!</b>\n\n👤 {name} (ID: {telegram_id})",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "❌ <b>Ошибка!</b> Пользователь с таким ID уже существует.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("user_remove:"))
async def remove_user_handler(callback: CallbackQuery):
    """Удаление пользователя"""
    _, user_id_str, role_str = callback.data.split(":")
    user_id = int(user_id_str)

    # Защита от удаления самого себя (если админ удаляет себя)
    if user_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете удалить сами себя!", show_alert=True)
        return

    success = await remove_user(user_id)

    if success:
        await callback.answer("✅ Пользователь удален", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)

    # Обновляем список
    await show_users_list(callback)
