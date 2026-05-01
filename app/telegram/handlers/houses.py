from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database import AsyncSessionLocal
from app.services.house_service import HouseService
from app.schemas.house import HouseCreate, HouseUpdate
from app.services.platform_sync_service import sync_all_platforms, get_last_sync_time, format_sync_results
from app.core.config import settings

router = Router()


class HouseStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_desc = State()
    waiting_for_capacity = State()


@router.callback_query(F.data == "admin:houses")
async def list_houses(callback: CallbackQuery):
    """Список домиков"""
    async with AsyncSessionLocal() as db:
        houses = await HouseService.get_all_houses(db)

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
    keyboard.append(
        [InlineKeyboardButton(text="🔄 Синхр. цены → все площадки", callback_data="admin:sync_all_platforms")]
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
    
    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)

    if not house:
        await callback.answer("Домик не найден")
        return

    price_str = f"{house.base_price} ₽/сут" if house.base_price else "Не задана"
    text = (
        f"🏠 <b>{house.name}</b>\n\n"
        f"📝 Описание: {house.description or 'Нет'}\n"
        f"👥 Вместимость: {house.capacity} чел.\n"
        f"💰 Базовая цена: {price_str}\n"
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

    # Use Schema
    house_in = HouseCreate(
        name=data["name"], 
        description=data["description"], 
        capacity=capacity
    )

    async with AsyncSessionLocal() as db:
        house = await HouseService.create_house(db, house_in)

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
    
    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)

    if not house:
        await callback.answer("House not found")
        return

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
    
    async with AsyncSessionLocal() as db:
        await HouseService.delete_house(db, house_id)
        
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


class EditHouseStates(StatesGroup):
    editing_name = State()
    editing_desc = State()
    editing_capacity = State()
    editing_base_price = State()
    editing_wifi = State()
    editing_instr = State()
    editing_photo = State()


class PriceStates(StatesGroup):
    waiting_label = State()
    waiting_price = State()
    waiting_date_from = State()
    waiting_date_to = State()


@router.callback_query(F.data.startswith("house:edit:"))
async def edit_house_menu(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        last_sync = await get_last_sync_time(db)

    if not house:
        await callback.answer("❌ Домик не найден")
        return

    price_label = f"{house.base_price:,} ₽" if house.base_price else "не задана"
    sync_label = f"⏱ {last_sync[:16].replace('T', ' ')} UTC" if last_sync else "не синхронизировано"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"house:edit_f:{house_id}:name")],
            [InlineKeyboardButton(text="📄 Описание", callback_data=f"house:edit_f:{house_id}:desc")],
            [InlineKeyboardButton(text="👥 Вместимость", callback_data=f"house:edit_f:{house_id}:cap")],
            [InlineKeyboardButton(
                text=f"💰 Базовая цена ({price_label})",
                callback_data=f"house:edit_f:{house_id}:base_price",
            )],
            [InlineKeyboardButton(text="📅 Сезонные цены", callback_data=f"house:prices:{house_id}")],
            [
                InlineKeyboardButton(text="📶 Wi-Fi", callback_data=f"house:edit_f:{house_id}:wifi"),
                InlineKeyboardButton(text="🔑 Инструкция", callback_data=f"house:edit_f:{house_id}:instr"),
            ],
            [InlineKeyboardButton(text="📸 Фото", callback_data=f"house:edit_f:{house_id}:photo")],
            [InlineKeyboardButton(
                text="🔄 Синхронизировать цены → площадки",
                callback_data=f"house:sync_platforms:{house_id}",
            )],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"house:view:{house_id}")],
        ]
    )

    await callback.message.edit_text(
        f"✏️ <b>Редактирование: {house.name}</b>\n"
        f"Последний синк площадок: <i>{sync_label}</i>\n\n"
        f"Выберите поле для изменения:",
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
    elif field == "base_price":
        await callback.message.edit_text("💰 Введите базовую цену за сутки (₽):")
        await state.set_state(EditHouseStates.editing_base_price)
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
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(name=message.text))
        
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_desc)
async def process_edit_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(description=message.text))
        
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_capacity)
async def process_edit_capacity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return

    data = await state.get_data()
    house_id = data["editing_house_id"]
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(capacity=int(message.text)))
        
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_wifi)
async def process_edit_wifi(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(wifi_info=message.text))
        
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_instr)
async def process_edit_instr(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(checkin_instruction=message.text))
        
    await finish_editing(message, house_id, state)


@router.message(EditHouseStates.editing_photo, F.photo)
async def process_edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    house_id = data["editing_house_id"]

    # Берем самое большое фото
    photo = message.photo[-1]
    file_id = photo.file_id
    
    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(promo_image_id=file_id))
        
    await finish_editing(message, house_id, state)


async def _auto_sync_after_price_change(house_id: int) -> None:
    """Фоновый синк цен на все площадки после любого изменения цены."""
    try:
        async with AsyncSessionLocal() as db:
            await sync_all_platforms(db, house_id=house_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("auto price sync failed house=%s: %s", house_id, e)


@router.message(EditHouseStates.editing_base_price)
async def process_edit_base_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число (цена в рублях).")
        return

    data = await state.get_data()
    house_id = data["editing_house_id"]

    async with AsyncSessionLocal() as db:
        await HouseService.update_house(db, house_id, HouseUpdate(base_price=int(message.text)))

    await finish_editing(message, house_id, state)
    await _auto_sync_after_price_change(house_id)


async def finish_editing(message: Message, house_id: int, state: FSMContext):
    await state.clear()
    await message.answer("✅ Изменения сохранены.")

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        
    price_str = f"{house.base_price} ₽/сут" if house.base_price else "Не задана"
    text = (
        f"🏠 <b>{house.name}</b>\n\n"
        f"📝 <b>Описание:</b> {house.description or 'Нет'}\n"
        f"👥 <b>Вместимость:</b> {house.capacity} чел.\n"
        f"💰 <b>Базовая цена:</b> {price_str}\n"
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


# --- Сезонные цены (CRUD) ---


@router.callback_query(F.data.startswith("house:prices:"))
async def list_house_prices(callback: CallbackQuery):
    """Список сезонных цен для домика"""
    house_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        if not house:
            await callback.answer("❌ Домик не найден")
            return

        from app.services.pricing_service import PricingService
        prices = await PricingService.get_prices_for_house(db, house_id)

    text = f"📅 <b>Сезонные цены: {house.name}</b>\n"
    text += f"💰 Базовая цена: {house.base_price} ₽/сут\n\n"

    if prices:
        for p in prices:
            text += (
                f"• <b>{p.label}</b>: {p.price_per_night} ₽/сут\n"
                f"  {p.date_from.strftime('%d.%m.%Y')} — {p.date_to.strftime('%d.%m.%Y')}\n"
            )
    else:
        text += "<i>Сезонных цен нет. Используется базовая цена.</i>\n"

    keyboard_rows = []
    for p in prices:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"❌ {p.label} ({p.price_per_night}₽)",
                callback_data=f"house:del_price:{p.id}:{house_id}",
            )
        ])

    keyboard_rows.append([
        InlineKeyboardButton(
            text="➕ Добавить сезон",
            callback_data=f"house:add_price:{house_id}",
        )
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"house:edit:{house_id}")
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("house:add_price:"))
async def start_add_price(callback: CallbackQuery, state: FSMContext):
    house_id = int(callback.data.split(":")[2])
    await state.update_data(price_house_id=house_id)
    await callback.message.edit_text(
        "📅 <b>Добавление сезонной цены</b>\n\n"
        "Введите название сезона (напр.: Новогодние, Лето, Майские):",
        parse_mode="HTML",
    )
    await state.set_state(PriceStates.waiting_label)
    await callback.answer()


@router.message(PriceStates.waiting_label)
async def process_price_label(message: Message, state: FSMContext):
    await state.update_data(price_label=message.text)
    await message.answer("💰 Введите цену за сутки (₽):")
    await state.set_state(PriceStates.waiting_price)


@router.message(PriceStates.waiting_price)
async def process_price_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    await state.update_data(price_amount=int(message.text))
    await message.answer("📅 Введите дату начала (ДД.ММ.ГГГГ, напр. 01.01.2027):")
    await state.set_state(PriceStates.waiting_date_from)


@router.message(PriceStates.waiting_date_from)
async def process_price_date_from(message: Message, state: FSMContext):
    from datetime import datetime as dt
    try:
        d = dt.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату как ДД.ММ.ГГГГ:")
        return
    await state.update_data(price_date_from=d.isoformat())
    await message.answer("📅 Введите дату окончания (ДД.ММ.ГГГГ):")
    await state.set_state(PriceStates.waiting_date_to)


@router.message(PriceStates.waiting_date_to)
async def process_price_date_to(message: Message, state: FSMContext):
    from datetime import datetime as dt, date as date_type
    try:
        d = dt.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату как ДД.ММ.ГГГГ:")
        return

    data = await state.get_data()
    date_from = date_type.fromisoformat(data["price_date_from"])

    if d <= date_from:
        await message.answer("❌ Дата окончания должна быть позже даты начала.")
        return

    house_id = data["price_house_id"]

    from app.services.pricing_service import PricingService
    async with AsyncSessionLocal() as db:
        price = await PricingService.create_price(
            db=db,
            house_id=house_id,
            label=data["price_label"],
            price_per_night=data["price_amount"],
            date_from=date_from,
            date_to=d,
        )

    await state.clear()
    await message.answer(
        f"✅ Сезон <b>{price.label}</b> добавлен: {price.price_per_night} ₽/сут\n"
        f"{price.date_from.strftime('%d.%m.%Y')} — {price.date_to.strftime('%d.%m.%Y')}\n\n"
        f"<i>Синхронизация с площадками запущена...</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 К ценам", callback_data=f"house:prices:{house_id}")],
            [InlineKeyboardButton(text="🔙 К домику", callback_data=f"house:edit:{house_id}")],
        ]),
        parse_mode="HTML",
    )
    await _auto_sync_after_price_change(house_id)


@router.callback_query(F.data.startswith("house:del_price:"))
async def delete_house_price(callback: CallbackQuery):
    parts = callback.data.split(":")
    price_id = int(parts[2])
    house_id = int(parts[3])

    from app.services.pricing_service import PricingService
    async with AsyncSessionLocal() as db:
        await PricingService.delete_price(db, price_id)

    await callback.answer("✅ Сезон удалён")
    await _auto_sync_after_price_change(house_id)
    callback.data = f"house:prices:{house_id}"
    await list_house_prices(callback)


# --- Синхронизация цен с площадками ---


@router.callback_query(F.data.startswith("house:sync_platforms:"))
async def sync_house_prices_to_platforms(callback: CallbackQuery):
    house_id = int(callback.data.split(":")[2])
    await callback.answer("🔄 Синхронизация...")

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        results = await sync_all_platforms(db, house_id=house_id)

    summary = format_sync_results(results)
    text = f"🔄 <b>Синхронизация цен: {house.name}</b>\n\n{summary}"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"house:edit:{house_id}")],
        ]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:sync_all_platforms")
async def sync_all_houses_prices(callback: CallbackQuery):
    """Синхронизировать цены ВСЕХ домиков на все площадки."""
    await callback.answer("🔄 Синхронизируем все домики...")

    async with AsyncSessionLocal() as db:
        results = await sync_all_platforms(db)

    summary = format_sync_results(results)
    text = f"🔄 <b>Синхронизация всех домиков</b>\n\n{summary}"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К домикам", callback_data="admin:houses")],
        ]),
        parse_mode="HTML",
    )
