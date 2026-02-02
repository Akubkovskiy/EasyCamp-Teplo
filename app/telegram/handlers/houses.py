from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.services.house_service import house_service
from app.core.config import settings

router = Router()


class HouseStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_desc = State()
    waiting_for_capacity = State()


@router.callback_query(F.data == "admin:houses")
async def list_houses(callback: CallbackQuery):
    """Список домиков"""
    houses = await house_service.get_all_houses()

    text = "🏠 <b>Управление домиками</b>\n\nСписок доступных объектов:"

    keyboard = []
    for h in houses:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🏠 {h.name}", callback_data=f"house:view:{h.id}"
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="➕ Добавить домик", callback_data="house:add")]
    )
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("house:view:"))
async def view_house(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])
    house = await house_service.get_house(house_id)

    if not house:
        await callback.answer("Домик не найден")
        return

    text = (
        f"🏠 <b>{house.name}</b>\n\n"
        f"📝 Описание: {house.description or 'Нет'}\n"
        f"👥 Вместимость: {house.capacity} чел.\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"house:edit:{house.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Удалить", callback_data=f"house:delete:{house.id}"
                )
            ],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin:houses")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# --- Создание домика (Create) ---


@router.callback_query(F.data == "house:add")
async def start_add_house(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"🏠 <b>Добавление нового домика</b>\n\nВведите название (например: {settings.project_name} 4):",
        parse_mode="HTML",
    )
    await state.set_state(HouseStates.waiting_for_name)
    await callback.answer()


@router.message(HouseStates.waiting_for_name)
async def process_house_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Введите описание домика:")
    await state.set_state(HouseStates.waiting_for_desc)


@router.message(HouseStates.waiting_for_desc)
async def process_house_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("👥 Введите вместимость (количество спальных мест):")
    await state.set_state(HouseStates.waiting_for_capacity)


@router.message(HouseStates.waiting_for_capacity)
async def process_house_capacity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return

    data = await state.get_data()
    capacity = int(message.text)

    house = await house_service.create_house(
        name=data["name"], description=data["description"], capacity=capacity
    )

    await message.answer(
        f"✅ <b>Домик {house.name} успешно добавлен!</b>\n"
        f"Вместимость: {house.capacity}\n"
        f"Описание: {house.description}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку", callback_data="admin:houses")]
            ]
        ),
        parse_mode="HTML",
    )
    await state.clear()


# --- Удаление домика (Delete) ---


@router.callback_query(F.data.startswith("house:delete:"))
async def confirm_delete_house(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])
    house = await house_service.get_house(house_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", callback_data=f"house:del_conf:{house_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет, оставить", callback_data=f"house:view:{house_id}"
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"⚠️ <b>Удалить домик {house.name}?</b>\n\n"
        "Внимание: это может повлиять на существующие бронирования!",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("house:del_conf:"))
async def execute_delete_house(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])
    await house_service.delete_house(house_id)
    await callback.message.edit_text(
        "✅ Домик удален.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку", callback_data="admin:houses")]
            ]
        ),
    )
    await callback.answer()


# --- Редактирование домика (Edit) ---


# --- Редактирование домика (Edit) ---


class EditHouseStates(StatesGroup):
    editing_name = State()
    editing_desc = State()
    editing_capacity = State()
    editing_wifi = State()
    editing_instr = State()
    editing_photo = State()


@router.callback_query(F.data.startswith("house:edit:"))
async def edit_house_menu(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])
    house = await house_service.get_house(house_id)

    if not house:
        await callback.answer("❌ Домик не найден")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Название", callback_data=f"house:edit_f:{house_id}:name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Описание", callback_data=f"house:edit_f:{house_id}:desc"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Вместимость", callback_data=f"house:edit_f:{house_id}:cap"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📶 Wi-Fi", callback_data=f"house:edit_f:{house_id}:wifi"
                ),
                InlineKeyboardButton(
                    text="🔑 Инструкция", callback_data=f"house:edit_f:{house_id}:instr"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📸 Фото", callback_data=f"house:edit_f:{house_id}:photo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data=f"house:view:{house_id}"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"✏️ <b>Редактирование: {house.name}</b>\nВыберите поле для изменения:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("house:edit_f:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    house_id = int(parts[2])
    field = parts[3]

    await state.update_data(editing_house_id=house_id)

    if field == "name":
        await callback.message.edit_text("📝 Введите новое название:")
        await state.set_state(EditHouseStates.editing_name)
    elif field == "desc":
        await callback.message.edit_text("📄 Введите новое описание:")
        await state.set_state(EditHouseStates.editing_desc)
    elif field == "cap":
        await callback.message.edit_text("👥 Введите новую вместимость (число):")
        await state.set_state(EditHouseStates.editing_capacity)
    elif field == "wifi":
        await callback.message.edit_text("📶 Введите данные Wi-Fi (SSID, пароль):")
        await state.set_state(EditHouseStates.editing_wifi)
    elif field == "instr":
        await callback.message.edit_text(
            "🔑 Введите инструкцию по заселению (код от кейбокса):"
        )
        await state.set_state(EditHouseStates.editing_instr)
    elif field == "photo":
        await callback.message.edit_text("📸 Отправьте фото домика (как картинку):")
        await state.set_state(EditHouseStates.editing_photo)

    await callback.answer()


@router.message(EditHouseStates.editing_name)
async def process_edit_name(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    await house_service.update_house(house_id, name=message.text)
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_desc)
async def process_edit_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    await house_service.update_house(house_id, description=message.text)
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_capacity)
async def process_edit_capacity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return

    data = await state.get_data()
    house_id = data["editing_house_id"]
    await house_service.update_house(house_id, capacity=int(message.text))
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_wifi)
async def process_edit_wifi(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    await house_service.update_house(house_id, wifi_info=message.text)
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_instr)
async def process_edit_instr(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    await house_service.update_house(house_id, checkin_instruction=message.text)
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_photo, F.photo)
async def process_edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]

    # Берем самое большое фото
    photo = message.photo[-1]
    file_id = photo.file_id

    await house_service.update_house(house_id, promo_image_id=file_id)
    await finish_editing(message, house_id, state)


async def finish_editing(message: Message, house_id: int, state: FSMContext):
    await state.clear()
    await message.answer("✅ Изменения сохранены.")

    house = await house_service.get_house(house_id)
    text = (
        f"🏠 <b>{house.name}</b>\n\n"
        f"📝 <b>Описание:</b> {house.description or 'Нет'}\n"
        f"👥 <b>Вместимость:</b> {house.capacity} чел.\n"
        f"📶 <b>Wi-Fi:</b> {house.wifi_info or 'Не задано'}\n"
        f"🔑 <b>Инструкция:</b> {'Задана' if house.checkin_instruction else 'Не задано'}\n"
        f"📸 <b>Фото:</b> {'Загружено' if house.promo_image_id else 'Нет'}\n"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"house:edit:{house.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Удалить", callback_data=f"house:delete:{house.id}"
                )
            ],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin:houses")],
        ]
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
