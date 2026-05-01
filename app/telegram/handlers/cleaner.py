from datetime import date, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, GlobalSetting
from app.telegram.auth.admin import get_user_name, is_admin, resolve_user_db_id
from app.jobs.cleaning_tasks_job import run_cleaning_tasks_cycle

# Статусы броней которые видит уборщица в расписании
ACTIVE_BOOKING_STATUSES = [
    BookingStatus.CONFIRMED,
    BookingStatus.PAID,
    BookingStatus.CHECKING_IN,
    BookingStatus.CHECKED_IN,
    BookingStatus.COMPLETED,
]

router = Router()


async def get_cleaning_schedule(start_date: date, end_date: date) -> list[Booking]:
    """Получает список броней, у которых выезд в заданном диапазоне"""
    async with AsyncSessionLocal() as session:
        query = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                and_(
                    Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                    Booking.check_out >= start_date,
                    Booking.check_out <= end_date,
                )
            )
            .order_by(Booking.check_out)
        )

        result = await session.execute(query)
        bookings = result.scalars().all()
        return list(bookings)


async def get_nearest_checkouts() -> str:
    """Формирует строку с ближайшими выездами по домам"""
    today = date.today()

    async with AsyncSessionLocal() as session:
        # Ищем ближайший выезд для каждого дома
        # Для простоты берем все выезды на неделю вперед
        prospect_date = today + timedelta(days=7)

        query = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                and_(
                    Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                    Booking.check_out >= today,
                    Booking.check_out <= prospect_date,
                )
            )
            .order_by(Booking.check_out)
        )

        result = await session.execute(query)
        bookings = list(result.scalars().all())

    if not bookings:
        return "Нет выездов на ближайшую неделю."

    # Группируем по датам, чтобы найти ближайшую уникальную дату выезда
    summary_lines = []

    # Сделаем просто список ближайших 3-5 выездов
    seen_houses = set()
    count = 0

    for b in bookings:
        if b.house_id in seen_houses:
            continue

        summary_lines.append(f"{b.house.name} ({b.check_out.strftime('%d.%m')})")
        seen_houses.add(b.house_id)
        count += 1
        if count >= 3:  # Показываем макс 3 дома в саммари
            break

    return ", ".join(summary_lines)


def get_cleaner_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Мои ЗАДАЧИ — назначенные CleaningTask (принять/начать/завершить)
            [
                InlineKeyboardButton(
                    text="✅ Задачи сегодня", callback_data="cleaner:tasks:today"
                ),
                InlineKeyboardButton(
                    text="✅ Задачи/7д", callback_data="cleaner:tasks:week"
                ),
            ],
            # Расписание ВЫЕЗДОВ гостей — информация о предстоящих уборках
            [
                InlineKeyboardButton(
                    text="📅 Выезды сегодня", callback_data="cleaner:schedule:today"
                ),
                InlineKeyboardButton(
                    text="📅 Выезды завтра", callback_data="cleaner:schedule:tomorrow"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Выезды/7д", callback_data="cleaner:schedule:week"
                ),
                InlineKeyboardButton(
                    text="📆 Выезды/месяц", callback_data="cleaner:schedule:month"
                ),
            ],
            [
                InlineKeyboardButton(text="🧾 Чек расходников", callback_data="cleaner:expense:new")
            ],
            [
                InlineKeyboardButton(text="💰 Мои выплаты", callback_data="cleaner:pay")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="cleaner:help"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="cleaner:settings"),
            ],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="cleaner:menu")],
        ]
    )


@router.callback_query(F.data == "cleaner:menu")
async def cleaner_menu_callback(callback: CallbackQuery):
    await show_cleaner_menu(callback, callback.from_user.id)
    # await callback.answer() # answer is handled in show_cleaner_menu if it's a callback


async def show_cleaner_menu(event: Message | CallbackQuery, user_id: int):
    """Главное меню уборщицы"""
    name = await get_user_name(user_id) or "друг"
    if isinstance(event, Message) and event.from_user:
        if event.from_user.first_name:
            name = await get_user_name(user_id) or event.from_user.first_name

    nearest_summary = await get_nearest_checkouts()

    text = (
        f"👋 <b>Добрый день, {name}!</b>\n\n"
        f"🧹 <b>Ближайшие выезды:</b>\n"
        f"{nearest_summary}\n\n"
        "Выберите период для просмотра графика:"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_cleaner_keyboard())
    elif isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=get_cleaner_keyboard())
        except Exception as e:
            # Если сообщение не изменилось (TelegramBadRequest), просто игнорируем ошибку
            if "message is not modified" in str(e):
                try:
                    await event.answer("✅ Данные актуальны", show_alert=False)
                except Exception:
                    pass  # Если query is too old, просто игнорируем
                return
            raise e

        # Успешное обновление
        try:
            await event.answer()
        except Exception:
            pass


async def get_all_upcoming_bookings() -> list[Booking]:
    """Получает ВСЕ предстоящие подтвержденные брони"""
    today = date.today()
    async with AsyncSessionLocal() as session:
        query = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                and_(
                    Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                    Booking.check_out >= today,
                )
            )
            .order_by(Booking.check_in)
        )  # Сортируем по заезду

        result = await session.execute(query)
        return list(result.scalars().all())


@router.callback_query(F.data.startswith("cleaner:schedule:"))
async def show_schedule(callback: CallbackQuery):
    """Показать график уборок"""
    mode = callback.data.split(":")[2]
    today = date.today()

    bookings = []
    title = ""
    is_list_view = False

    if mode == "today":
        bookings = await get_cleaning_schedule(today, today)
        title = "на СЕГОДНЯ"
    elif mode == "tomorrow":
        bookings = await get_cleaning_schedule(
            today + timedelta(days=1), today + timedelta(days=1)
        )
        title = "на ЗАВТРА"
    elif mode == "week":
        bookings = await get_cleaning_schedule(today, today + timedelta(days=7))
        title = "на НЕДЕЛЮ"
    elif mode == "month":
        days = await _get_cleaner_schedule_days(callback.from_user.id)
        bookings = await get_cleaning_schedule(today, today + timedelta(days=days))
        title = f"на {days} дней"
        is_list_view = True
    elif mode == "all":
        bookings = await get_all_upcoming_bookings()
        title = "ВСЕ БРОНИ"
        is_list_view = True

    if not bookings:
        try:
            await callback.message.edit_text(
                f"🧹 <b>График: {title}</b>\n\n✅ Броней/выездов нет.",
                reply_markup=get_cleaner_keyboard(),
                parse_mode="HTML",
            )
        except Exception:
            pass  # Ignore message not modified
        await callback.answer()
        return

    text = f"📅 <b>Выезды гостей {title}</b>\n<i>(информация о предстоящих уборках)</i>\n\n"

    # Режим списка всех броней (Компактно)
    if is_list_view:
        current_month = None
        months_ru = {
            1: "Январь",
            2: "Февраль",
            3: "Март",
            4: "Апрель",
            5: "Май",
            6: "Июнь",
            7: "Июль",
            8: "Август",
            9: "Сентябрь",
            10: "Октябрь",
            11: "Ноябрь",
            12: "Декабрь",
        }

        for b in bookings:
            # Группировка по месяцам
            if b.check_in.month != current_month:
                current_month = b.check_in.month
                month_name = months_ru.get(current_month, "")
                text += f"\n📅 <b>{month_name}</b>\n"

            check_in_str = b.check_in.strftime("%d.%m")
            check_out_str = b.check_out.strftime("%d.%m")
            text += f"🏠 {b.house.name} | {check_in_str} - {check_out_str}\n"

    else:
        # Режим уборок (Подробно с телефоном)
        days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
        current_date = None

        for b in bookings:
            if b.check_out != current_date:
                current_date = b.check_out
                weekday = days_map[current_date.weekday()]
                text += f"\n📅 <b>{current_date.strftime('%d.%m')} ({weekday})</b>\n"

            text += (
                f"   🏠 <b>{b.house.name}</b> | 👥 {b.guests_count} чел\n"
                f"   📞 {b.guest_phone}\n"
                f"   🕒 Выезд до 12:00\n"
            )

    try:
        await callback.message.edit_text(
            text, reply_markup=get_cleaner_keyboard(), parse_mode="HTML"
        )
    except Exception:
        await callback.answer("✅ Данные актуальны")
        return

    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:confirm:"))
async def confirm_cleaning(callback: CallbackQuery):
    """Подтверждение выхода на смену"""
    # callback.data = cleaner:confirm:2025-01-12
    date_str = callback.data.split(":")[2]

    # Редактируем сообщение (убираем кнопки и ставим галочку)
    # Можно сохранить оригинал сообщения и добавить в начало статус
    current_text = callback.message.text
    # Удаляем футер с просьбой подтвердить
    clean_text = current_text.replace("⚠️ Пожалуйста, подтвердите выход на смену!", "")

    new_text = f"✅ <b>ВЫ ПОДТВЕРДИЛИ ВЫХОД {date_str}</b>\n\n{clean_text}"

    await callback.message.edit_text(new_text, reply_markup=None)
    await callback.answer("✅ Спасибо, принято!")


@router.callback_query(F.data.startswith("cleaner:decline:"))
async def decline_cleaning(callback: CallbackQuery):
    """Отказ от смены"""
    date_str = callback.data.split(":")[2]
    cleaner_name = callback.from_user.first_name or "Неизвестно"
    cleaner_username = callback.from_user.username

    # 1. Ответ уборщице
    await callback.message.edit_text(
        f"⚠️ <b>Отказ от смены {date_str}</b>\n\n"
        "Информация передана администратору. Пожалуйста, оставайтесь на связи.",
        reply_markup=None,
    )

    # 2. Оповещение ВСЕХ администраторов
    from app.telegram.auth.admin import get_all_users, UserRole
    from app.core.config import settings

    admin_users = await get_all_users()
    admin_ids = {u.telegram_id for u in admin_users if u.role == UserRole.ADMIN}
    # Добавляем главного админа
    admin_ids.add(settings.telegram_chat_id)

    username_text = f"(@{cleaner_username})" if cleaner_username else ""
    alert_text = (
        f"🚨 <b>SOS! Уборщица отказалась от смены!</b>\n\n"
        f"📅 Дата выезда: <b>{date_str}</b>\n"
        f"👤 Кто: <b>{cleaner_name}</b> {username_text}\n\n"
        "❗ <b>Срочно свяжитесь для замены!</b>"
    )

    for admin_id in admin_ids:
        try:
            await callback.bot.send_message(admin_id, alert_text)
        except Exception:
            pass

    await callback.answer("Администратор оповещен", show_alert=True)


async def _get_cleaner_schedule_days(telegram_id: int) -> int:
    db_id = await resolve_user_db_id(None, telegram_id)
    if not db_id:
        return 30
    async with AsyncSessionLocal() as s:
        setting = await s.get(GlobalSetting, f"cleaner_schedule_days_{db_id}")
        if setting and setting.value:
            try:
                return int(setting.value)
            except ValueError:
                pass
    return 30


@router.callback_query(F.data == "cleaner:settings")
async def cleaner_settings_menu(callback: CallbackQuery):
    if not callback.from_user:
        return
    days = await _get_cleaner_schedule_days(callback.from_user.id)
    text = (
        f"⚙️ <b>Мои настройки</b>\n\n"
        f"📆 Расписание «На месяц»: <b>{days} дней</b>\n\n"
        "Выберите на сколько дней вперёд показывать уборки:"
    )
    rows = [
        [
            InlineKeyboardButton(text="7 дней", callback_data="cleaner:settings:days:7"),
            InlineKeyboardButton(text="14 дней", callback_data="cleaner:settings:days:14"),
            InlineKeyboardButton(text="30 дней", callback_data="cleaner:settings:days:30"),
            InlineKeyboardButton(text="60 дней", callback_data="cleaner:settings:days:60"),
        ],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")],
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:settings:days:"))
async def cleaner_settings_days_save(callback: CallbackQuery):
    if not callback.from_user:
        return
    days = int(callback.data.split(":")[-1])
    db_id = await resolve_user_db_id(None, callback.from_user.id)
    if db_id:
        async with AsyncSessionLocal() as s:
            key = f"cleaner_schedule_days_{db_id}"
            setting = await s.get(GlobalSetting, key)
            if setting:
                setting.value = str(days)
            else:
                s.add(GlobalSetting(key=key, value=str(days), description=f"Schedule days for cleaner {db_id}"))
            await s.commit()
    await callback.answer(f"Сохранено: {days} дней")
    await cleaner_settings_menu(callback)


HELP_TEXT = """❓ <b>Как работает ваш личный кабинет</b>

━━━━━━━━━━━━━━━━
🧹 <b>ЗАДАЧИ НА УБОРКУ</b>
━━━━━━━━━━━━━━━━
1. Когда гость выезжает — бот присылает вам задачу
2. Нажмите <b>«✅ Принять»</b> чтобы взяться за неё
3. Когда начали убираться — нажмите <b>«🚿 Начать уборку»</b>
4. Закончили — нажмите <b>«✅ Завершить»</b>

📌 Кнопка <b>«📌 Мои задачи»</b> — показывает активные задачи
📌 Кнопка <b>«🗓 Мои задачи/7д»</b> — задачи на неделю вперёд

━━━━━━━━━━━━━━━━
☑️ <b>ЧЕКЛИСТ</b>
━━━━━━━━━━━━━━━━
• Нажмите <b>«☑️ Чеклист»</b> во время уборки
• Отмечайте каждый пункт — это подтверждение качества
• Пункт <b>«Нехватка расходников»</b> — автоматически оповещает администратора
• После оповещения можно сразу отправить фото нехватки прямо в чат

━━━━━━━━━━━━━━━━
📸 <b>ФОТО</b>
━━━━━━━━━━━━━━━━
• Отправьте любое фото в чат — оно само прикрепится к активной уборке
• Можно отправить несколько фото подряд
• Фотографируйте итог уборки: кровати, ванную, кухню

━━━━━━━━━━━━━━━━
💰 <b>ДОПОЛНИТЕЛЬНАЯ РАБОТА</b>
━━━━━━━━━━━━━━━━
• В задаче нажмите <b>«💰 Доп. работа»</b>
• Готовые варианты (например «Отвезти белье») — начисляются <b>сразу автоматически</b>
• <b>«Описать своё»</b> — отправляет запрос администратору, он назначит сумму

━━━━━━━━━━━━━━━━
💵 <b>ВЫПЛАТЫ</b>
━━━━━━━━━━━━━━━━
• Кнопка <b>«💰 Мои выплаты»</b> — ваш баланс и история
• <b>«📋 История уборок»</b> — все выполненные уборки по месяцам с суммами
• <b>«💸 Запросить выплату»</b> — отправляет уведомление администратору

⚠️ <b>Перед запросом выплаты обязательно заполните реквизиты СБП!</b>

━━━━━━━━━━━━━━━━
⚙️ <b>МОИ РЕКВИЗИТЫ (СБП)</b>
━━━━━━━━━━━━━━━━
• Выплаты → <b>«⚙️ Мои реквизиты»</b>
• Укажите банк и номер телефона
• Без реквизитов запросить выплату <b>не получится</b>"""


@router.callback_query(F.data == "cleaner:help")
async def cleaner_help(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cleaner:menu")],
        ]),
    )
    await callback.answer()


@router.message(Command("cleaner_tasks_sync"))
async def cleaner_tasks_sync_now(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return
    await run_cleaning_tasks_cycle()
    await message.answer("✅ Генерация задач уборки и рассылка выполнены")
