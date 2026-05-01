"""Self-service бронирование гостя (Phase G10.1).

Гость:
1) выбирает даты через `guest:availability` (общий availability flow)
2) видит карточки домиков с кнопкой `guest:book:{house_id}`
3) если авторизован — сразу к выбору кол-ва гостей
4) если не авторизован — просим контакт (создаём User с ролью GUEST)
5) выбирает кол-во гостей -> карточка подтверждения -> создаём Booking(NEW)
6) админ получает уведомление с кнопками confirm/reject
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import (
    Booking,
    BookingSource,
    BookingStatus,
    User,
    UserRole,
)
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService
from app.services.house_service import HouseService
from app.services.pricing_service import PricingService
from app.telegram.auth.admin import (
    add_user,
    get_all_users,
    is_admin,
    refresh_users_cache,
)
from app.telegram.menus.guest import request_contact_keyboard
from app.telegram.state.availability import availability_states
from app.utils.phone import normalize_phone


router = Router()
logger = logging.getLogger(__name__)


# user_id -> {house_id, check_in, check_out, guest_name?, guest_phone?,
#             guests_count?, total_price?, waiting_for_contact?}
_guest_book_pending: dict[int, dict] = {}


def _is_pending_book_contact(message: Message) -> bool:
    """Filter: contact share только от гостей в pending booking flow.
    Если фильтр не пройден, диспетчер передаст message в guest.handle_contact."""
    if not message.from_user:
        return False
    state = _guest_book_pending.get(message.from_user.id)
    return bool(state and state.get("waiting_for_contact"))


async def _user_contact_from_db(telegram_id: int) -> dict | None:
    """Возвращает (name, phone) из User, если уже сохранён."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
    if user and user.phone:
        return {
            "guest_name": (user.name or "Гость").strip(),
            "guest_phone": user.phone,
        }
    return None


def _build_guests_count_kb(max_capacity: int) -> InlineKeyboardMarkup:
    """Кнопки выбора кол-ва гостей в пределах вместимости домика."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for n in range(1, max(max_capacity, 1) + 1):
        row.append(
            InlineKeyboardButton(
                text=str(n), callback_data=f"guest:book:guests:{n}"
            )
        )
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="❌ Отменить", callback_data="guest:book:cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_admin_booking_notification(
    bot,
    booking: Booking,
    house_name: str,
    guest_tg: int,
    telegram_full_name: str,
    username: str | None,
):
    """Уведомление админам с кнопками confirm/reject."""
    users = await get_all_users()
    admin_ids = {
        u.telegram_id
        for u in users
        if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id
    }
    admin_ids.add(settings.telegram_chat_id)

    nights = (booking.check_out - booking.check_in).days
    text = (
        "🆕 <b>Новая бронь от гостя</b>\n\n"
        f"#{booking.id} · {house_name}\n"
        f"📅 {booking.check_in.strftime('%d.%m.%Y')} — "
        f"{booking.check_out.strftime('%d.%m.%Y')} ({nights} сут.)\n"
        f"👥 {booking.guests_count}\n"
        f"💰 {int(booking.total_price):,} ₽\n\n"
        f"Гость: {booking.guest_name} ({booking.guest_phone})\n"
        f"Telegram: {telegram_full_name} "
        f"(@{username or '-'}) · <code>{guest_tg}</code>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"guest:book:admin_confirm:{booking.id}:{guest_tg}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"guest:book:admin_reject:{booking.id}:{guest_tg}",
            ),
        ]]
    )
    for aid in admin_ids:
        try:
            await bot.send_message(aid, text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"failed to notify admin {aid}: {e}")


async def _ask_guests_count(message_or_callback, house_id: int):
    """Шлём гостю экран с выбором кол-ва гостей.
    Принимаем либо CallbackQuery (edit_text), либо Message (answer)."""
    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
    if not house:
        target = (
            message_or_callback.message
            if isinstance(message_or_callback, CallbackQuery)
            else message_or_callback
        )
        await target.answer("❌ Домик не найден")
        return

    text = (
        f"🏠 <b>{house.name}</b>\n"
        f"Сколько будет гостей? (макс. {house.capacity})"
    )
    kb = _build_guests_count_kb(house.capacity)

    if isinstance(message_or_callback, CallbackQuery):
        try:
            await message_or_callback.message.edit_text(
                text, reply_markup=kb, parse_mode="HTML"
            )
        except Exception:
            await message_or_callback.message.answer(
                text, reply_markup=kb, parse_mode="HTML"
            )
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=kb, parse_mode="HTML")


def _is_book_house_callback(callback: CallbackQuery) -> bool:
    """Match `guest:book:<digits>` strictly. Excludes :guests:, :confirm,
    :cancel, :admin_confirm:, :admin_reject:."""
    if not callback.data:
        return False
    parts = callback.data.split(":")
    return (
        len(parts) == 3
        and parts[0] == "guest"
        and parts[1] == "book"
        and parts[2].isdigit()
    )


@router.callback_query(_is_book_house_callback)
async def guest_book_start(callback: CallbackQuery):
    """Entry: гость нажал «Забронировать» в карточке домика."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id

    # admin использует существующий админский флоу через booking:create:
    if is_admin(user_id):
        await callback.answer(
            "Админ использует обычный flow создания брони", show_alert=True
        )
        return

    parts = callback.data.split(":")
    try:
        house_id = int(parts[2])
    except (IndexError, ValueError):
        return

    avail = availability_states.get(user_id)
    if not avail or not avail.check_in or not avail.check_out:
        await callback.answer(
            "❌ Сначала выберите даты — нажмите "
            "«📅 Проверить даты и забронировать».",
            show_alert=True,
        )
        return

    _guest_book_pending[user_id] = {
        "house_id": house_id,
        "check_in": avail.check_in,
        "check_out": avail.check_out,
    }

    contact = await _user_contact_from_db(user_id)
    if contact:
        _guest_book_pending[user_id].update(contact)
        await _ask_guests_count(callback, house_id)
        return

    _guest_book_pending[user_id]["waiting_for_contact"] = True
    await callback.message.answer(
        "📱 Чтобы оформить бронь — поделитесь номером телефона.\n"
        "Мы свяжем бронь с вашим Telegram, и админ напишет вам после подтверждения.",
        reply_markup=request_contact_keyboard(),
    )
    await callback.answer()


@router.message(F.contact, _is_pending_book_contact)
async def guest_book_contact(message: Message):
    """Контакт получен в self-service потоке (не login). Создаём User
    с ролью GUEST и продолжаем поток к выбору кол-ва гостей."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    pending = _guest_book_pending.get(user_id)
    if not pending or not pending.get("waiting_for_contact"):
        return

    contact = message.contact
    if contact.user_id != user_id:
        await message.answer(
            "⚠️ Пожалуйста, отправьте СВОЙ контакт через кнопку внизу."
        )
        return

    clean_phone = normalize_phone(contact.phone_number)
    name = (
        contact.first_name
        or message.from_user.first_name
        or "Гость"
    ).strip() or "Гость"

    # add_user идемпотентен по уникальному telegram_id (вернёт False, если уже есть)
    await add_user(
        telegram_id=user_id,
        role=UserRole.GUEST,
        name=name,
        phone=clean_phone,
    )
    await refresh_users_cache()

    # помечаем авторизованным в guest-state — чтобы личный кабинет открылся
    # после подтверждения брони
    try:
        from app.telegram.handlers.guest import set_guest_auth, set_guest_context

        set_guest_auth(user_id, True)
        set_guest_context(user_id, "guest_cabinet")
    except Exception:
        pass

    pending.pop("waiting_for_contact", None)
    pending["guest_name"] = name
    pending["guest_phone"] = clean_phone

    await message.answer("✅ Принято.", reply_markup=ReplyKeyboardRemove())
    await _ask_guests_count(message, pending["house_id"])


@router.callback_query(F.data.startswith("guest:book:guests:"))
async def guest_book_guests_count(callback: CallbackQuery):
    """Выбрано кол-во гостей -> показ карточки подтверждения."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    pending = _guest_book_pending.get(user_id)
    if not pending:
        await callback.answer(
            "Сессия бронирования истекла. Начните заново.", show_alert=True
        )
        return

    try:
        guests_count = int(callback.data.split(":")[3])
    except (IndexError, ValueError):
        return

    house_id = pending["house_id"]
    check_in = pending["check_in"]
    check_out = pending["check_out"]

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        stay = await PricingService.calculate_stay_total(
            db, house_id, check_in, check_out
        )

    if not house:
        await callback.answer("❌ Домик не найден", show_alert=True)
        return
    if guests_count > house.capacity:
        await callback.answer(
            f"Этот домик до {house.capacity} гостей", show_alert=True
        )
        return

    pending["guests_count"] = guests_count
    nights = (check_out - check_in).days
    total = int(stay.get("total", 0))
    pending["total_price"] = Decimal(str(total))

    text = (
        "🧾 <b>Проверьте бронь</b>\n\n"
        f"🏠 <b>{house.name}</b>\n"
        f"📅 {check_in.strftime('%d.%m.%Y')} — "
        f"{check_out.strftime('%d.%m.%Y')} ({nights} сут.)\n"
        f"👥 Гостей: {guests_count}\n"
        f"💰 Сумма: <b>{total:,} ₽</b>\n\n"
        f"Гость: {pending.get('guest_name', '—')}\n"
        f"Телефон: {pending.get('guest_phone', '—')}\n\n"
        "Нажмите «Подтвердить» — заявка уйдёт администратору."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить", callback_data="guest:book:confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="guest:book:cancel"
                )
            ],
        ]
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:book:confirm")
async def guest_book_confirm(callback: CallbackQuery):
    """Финальное подтверждение -> Booking(NEW) + admin notification."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    pending = _guest_book_pending.get(user_id)
    if not pending or not pending.get("guests_count"):
        await callback.answer("Сессия не найдена, начните заново", show_alert=True)
        return

    house_id = pending["house_id"]
    check_in = pending["check_in"]
    check_out = pending["check_out"]
    guests_count = pending["guests_count"]
    guest_name = pending.get("guest_name", "Гость")
    guest_phone = pending.get("guest_phone", "")
    total_price = pending.get("total_price", Decimal(0))

    async with AsyncSessionLocal() as db:
        is_avail = await BookingService.check_availability(
            db, house_id=house_id, check_in=check_in, check_out=check_out
        )
        if not is_avail:
            _guest_book_pending.pop(user_id, None)
            try:
                await callback.message.edit_text(
                    "❌ К сожалению, эти даты только что заняли. "
                    "Попробуйте другие.",
                )
            except Exception:
                pass
            await callback.answer()
            return

        booking = await BookingService.create_booking(
            db,
            BookingCreate(
                house_id=house_id,
                guest_name=guest_name,
                guest_phone=guest_phone,
                check_in=check_in,
                check_out=check_out,
                guests_count=guests_count,
                total_price=total_price,
                advance_amount=Decimal(0),
                status=BookingStatus.NEW,
                source=BookingSource.TELEGRAM,
            ),
        )
        if not booking:
            _guest_book_pending.pop(user_id, None)
            try:
                await callback.message.edit_text(
                    "❌ Не удалось создать бронь. Попробуйте ещё раз "
                    "или свяжитесь с админом."
                )
            except Exception:
                pass
            await callback.answer()
            return

        house = await HouseService.get_house_by_id(db, house_id)
        house_name = house.name if house else f"Дом {house_id}"

    _guest_book_pending.pop(user_id, None)

    try:
        await callback.message.edit_text(
            f"✅ <b>Заявка отправлена!</b>\n\n"
            f"Бронь #{booking.id} ожидает подтверждения администратора.\n"
            "Мы напишем, как только админ подтвердит — после этого "
            "откроется кнопка оплаты.",
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"✅ Заявка #{booking.id} отправлена. Ожидайте подтверждения админа."
        )
    await callback.answer("Заявка отправлена")

    await _send_admin_booking_notification(
        callback.bot,
        booking,
        house_name=house_name,
        guest_tg=user_id,
        telegram_full_name=callback.from_user.full_name,
        username=callback.from_user.username,
    )


@router.callback_query(F.data == "guest:book:cancel")
async def guest_book_cancel(callback: CallbackQuery):
    if not callback.from_user:
        return
    _guest_book_pending.pop(callback.from_user.id, None)
    try:
        await callback.message.edit_text("❌ Бронирование отменено.")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("guest:book:admin_confirm:"))
async def guest_book_admin_confirm(callback: CallbackQuery):
    """Админ подтверждает бронь -> CONFIRMED + notify guest."""
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        return
    try:
        booking_id = int(parts[3])
        guest_tg = int(parts[4])
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        if booking.status != BookingStatus.NEW:
            await callback.answer(
                f"Бронь уже в статусе {booking.status.value}", show_alert=True
            )
            return
        booking.status = BookingStatus.CONFIRMED
        booking.updated_at = datetime.now(timezone.utc)
        await session.commit()

    from app.services.cleaner_notify import notify_cleaners_new_booking
    await notify_cleaners_new_booking(callback.bot, booking)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await callback.message.answer(f"✅ Бронь #{booking_id} подтверждена")
    except Exception:
        pass

    pay_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплата", callback_data="guest:pay")],
            [InlineKeyboardButton(text="🏠 Моя бронь", callback_data="guest:my_booking")],
        ]
    )
    try:
        await callback.bot.send_message(
            guest_tg,
            f"✅ Ваша бронь #{booking_id} подтверждена!\n\n"
            "Откройте «Оплата», чтобы внести предоплату и прислать чек.",
            reply_markup=pay_kb,
        )
    except Exception as e:
        logger.warning(f"failed to notify guest {guest_tg}: {e}")
    await callback.answer("Подтверждено")


@router.callback_query(F.data.startswith("guest:book:admin_reject:"))
async def guest_book_admin_reject(callback: CallbackQuery):
    """Админ отклоняет бронь -> CANCELLED + notify guest."""
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        return
    try:
        booking_id = int(parts[3])
        guest_tg = int(parts[4])
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return

        # cancel_booking сам обновит статус, разблокирует Avito и пушнёт sheets
        ok = await BookingService.cancel_booking(session, booking_id)
        if not ok:
            await callback.answer("Не удалось отменить", show_alert=True)
            return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await callback.message.answer(f"❌ Бронь #{booking_id} отклонена")
    except Exception:
        pass
    try:
        await callback.bot.send_message(
            guest_tg,
            f"⚠️ Ваша бронь #{booking_id} отклонена администратором.\n"
            "Если вы хотите уточнить причину — напишите нам через "
            "«Связаться с нами» в меню.",
        )
    except Exception as e:
        logger.warning(f"failed to notify guest {guest_tg}: {e}")
    await callback.answer("Отклонено")


# -------------------------------------------------
# Site-lead confirm/reject (from website bookings)
# -------------------------------------------------


@router.callback_query(F.data.startswith("site_lead:confirm:"))
async def site_lead_confirm(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    try:
        booking_id = int(parts[2])
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        if booking.status != BookingStatus.NEW:
            await callback.answer(
                f"Бронь уже в статусе {booking.status.value}", show_alert=True
            )
            return
        booking.status = BookingStatus.CONFIRMED
        booking.updated_at = datetime.now(timezone.utc)
        await session.commit()

    from app.services.cleaner_notify import notify_cleaners_new_booking
    await notify_cleaners_new_booking(callback.bot, booking)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await callback.message.answer(f"✅ Бронь #{booking_id} (сайт) подтверждена")
    except Exception:
        pass
    await callback.answer("Подтверждено")


@router.callback_query(F.data.startswith("site_lead:reject:"))
async def site_lead_reject(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    try:
        booking_id = int(parts[2])
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        ok = await BookingService.cancel_booking(session, booking_id)
        if not ok:
            await callback.answer("Не удалось отменить", show_alert=True)
            return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await callback.message.answer(f"❌ Бронь #{booking_id} (сайт) отклонена")
    except Exception:
        pass
    await callback.answer("Отклонено")


# -------------------------------------------------
# G10.2 — Self-service cancel
# -------------------------------------------------


async def _guest_cancel_admin_link_kb() -> InlineKeyboardMarkup:
    """Кнопки для случая «слишком близко к заезду» — гость не может
    отменить сам, перенаправляем к админу."""
    rows = [
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="guest:contact_admin")],
        [InlineKeyboardButton(text="🔙 К брони", callback_data="guest:my_booking")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("guest:cancel:start:"))
async def guest_cancel_start(callback: CallbackQuery):
    """Гость нажал «Отменить бронь»: проверяем окно отмены, спрашиваем подтверждение."""
    if not callback.from_user or not callback.message:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        return
    try:
        booking_id = int(parts[3])
    except ValueError:
        return

    from app.services.global_settings import (
        can_guest_self_cancel,
        get_guest_cancel_window_days,
    )

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return

        if booking.status in {BookingStatus.CANCELLED, BookingStatus.COMPLETED}:
            await callback.answer(
                f"Бронь уже {booking.status.value}", show_alert=True
            )
            return

        # Проверяем что бронь действительно принадлежит этому гостю.
        # Сравниваем по нормализованному телефону, как в auth flow.
        from app.utils.phone import phones_match

        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.phone or not phones_match(user.phone, booking.guest_phone):
            await callback.answer(
                "❌ Это не ваша бронь", show_alert=True
            )
            return

        window_days = await get_guest_cancel_window_days(session)

    today = datetime.now().date()
    days_to_checkin = (booking.check_in - today).days

    if not can_guest_self_cancel(days_to_checkin, window_days):
        text = (
            f"⚠️ <b>До заезда осталось {max(0, days_to_checkin)} дн.</b>\n"
            f"Самостоятельная отмена возможна только если до заезда "
            f"больше {window_days} дн.\n\n"
            "Свяжитесь с администратором — возможно начисление штрафа "
            "согласно условиям брони."
        )
        kb = await _guest_cancel_admin_link_kb()
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return

    confirm_text = (
        f"❓ <b>Отменить бронь #{booking.id}?</b>\n\n"
        f"📅 {booking.check_in.strftime('%d.%m.%Y')} — "
        f"{booking.check_out.strftime('%d.%m.%Y')}\n"
        f"До заезда осталось <b>{days_to_checkin} дн.</b>\n\n"
        "После отмены даты вернутся в продажу."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, отменить",
                    callback_data=f"guest:cancel:confirm:{booking.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Нет, оставить", callback_data="guest:my_booking"
                )
            ],
        ]
    )
    try:
        await callback.message.edit_text(confirm_text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(confirm_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("guest:cancel:confirm:"))
async def guest_cancel_confirm(callback: CallbackQuery):
    """Подтверждение отмены — фактически отменяет бронь и нотифицирует админа."""
    if not callback.from_user or not callback.message:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        return
    try:
        booking_id = int(parts[3])
    except ValueError:
        return

    from app.services.global_settings import (
        can_guest_self_cancel,
        get_guest_cancel_window_days,
    )
    from app.utils.phone import phones_match

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        if booking.status == BookingStatus.CANCELLED:
            await callback.answer("Уже отменена", show_alert=True)
            return

        # Повторно проверяем «свою» бронь и окно отмены — защита от
        # callback-replay из старых сообщений.
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.phone or not phones_match(user.phone, booking.guest_phone):
            await callback.answer("Это не ваша бронь", show_alert=True)
            return

        window_days = await get_guest_cancel_window_days(session)
        today = datetime.now().date()
        days_to_checkin = (booking.check_in - today).days
        if not can_guest_self_cancel(days_to_checkin, window_days):
            await callback.answer(
                "Окно самостоятельной отмены закрыто, свяжитесь с админом",
                show_alert=True,
            )
            return

        # Снимок данных для уведомления админа (после cancel объект «отстанет»)
        snapshot = {
            "house_id": booking.house_id,
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "guest_name": booking.guest_name,
            "guest_phone": booking.guest_phone,
        }

        ok = await BookingService.cancel_booking(session, booking_id)
        if not ok:
            await callback.answer("Не удалось отменить", show_alert=True)
            return

        house = await HouseService.get_house_by_id(session, snapshot["house_id"])
        house_name = house.name if house else f"Дом {snapshot['house_id']}"

    # Уведомляем гостя
    try:
        await callback.message.edit_text(
            f"✅ Бронь #{booking_id} отменена.\n"
            "Спасибо, что предупредили заранее.",
        )
    except Exception:
        pass
    await callback.answer("Отменено")

    # Уведомляем админов
    users = await get_all_users()
    admin_ids = {
        u.telegram_id
        for u in users
        if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id
    }
    admin_ids.add(settings.telegram_chat_id)

    text = (
        "🚫 <b>Гость отменил бронь</b>\n\n"
        f"#{booking_id} · {house_name}\n"
        f"📅 {snapshot['check_in'].strftime('%d.%m.%Y')} — "
        f"{snapshot['check_out'].strftime('%d.%m.%Y')}\n"
        f"Гость: {snapshot['guest_name']} ({snapshot['guest_phone']})\n"
        f"Telegram: <code>{callback.from_user.id}</code>\n\n"
        f"Даты освобождены."
    )
    for aid in admin_ids:
        try:
            await callback.bot.send_message(aid, text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"failed to notify admin {aid}: {e}")
