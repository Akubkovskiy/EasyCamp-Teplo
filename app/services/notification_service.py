import logging
import asyncio
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Optional, List, Any

from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from aiogram.types import InlineKeyboardMarkup

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, User, UserRole
from app.telegram.bot import bot

logger = logging.getLogger(__name__)


@dataclass
class NotificationRule:
    """Правило уведомления"""

    name: str
    reference_field: str  # 'check_in' или 'check_out'
    days_offset: int  # 1 = завтра, 0 = сегодня, -1 = вчера
    recipient_type: str  # 'cleaner', 'guest', 'admin'
    message_func: Callable[[List[Booking], Any], str]  # (bookings, recipient) -> text
    keyboard_func: Optional[
        Callable[[List[Booking], Any], Optional[InlineKeyboardMarkup]]
    ] = None


class NotificationService:
    """Сервис для рассылки уведомлений по правилам"""

    async def process_rule(self, rule: NotificationRule):
        logger.info(f"Processing notification rule: {rule.name}")

        target_date = date.today() + timedelta(days=rule.days_offset)

        async with AsyncSessionLocal() as session:
            # 1. Получаем подходящие брони
            # Динамически выбираем поле для фильтрации
            field_attr = getattr(Booking, rule.reference_field, None)
            if not field_attr:
                logger.error(f"Invalid reference field: {rule.reference_field}")
                return

            query = (
                select(Booking)
                .options(joinedload(Booking.house))
                .where(
                    and_(
                        Booking.status.in_(
                            [
                                BookingStatus.CONFIRMED,
                                BookingStatus.PAID,
                                BookingStatus.CHECKING_IN,
                                BookingStatus.CHECKED_IN,
                                BookingStatus.COMPLETED,
                            ]
                        ),
                        field_attr == target_date,
                    )
                )
            )
            result = await session.execute(query)
            bookings = result.scalars().all()

            if not bookings and rule.recipient_type != "cleaner":
                # Для уборщиц (cleaner) мы можем хотеть отправить "отмену" если ничего нет,
                # но пока следуем логике "нет броней - нет уведомлений", кроме случая когда мы группируем все брони для одного получателя.
                # В текущей реализации мы обрабатываем список броней.
                logger.debug(f"No bookings found for rule {rule.name} on {target_date}")
                return

            if not bookings:
                # Если броней нет, то для уборщиков можно ничего не слать.
                return

            # 2. Определяем получателей и отправляем
            if rule.recipient_type == "cleaner":
                await self._notify_cleaners(session, bookings, rule)
            elif rule.recipient_type == "guest":
                await self._notify_guests(session, bookings, rule)
            elif rule.recipient_type == "admin":
                await self._notify_admins(session, bookings, rule)
            else:
                logger.error(f"Unknown recipient type: {rule.recipient_type}")

    async def _notify_cleaners(
        self, session, bookings: List[Booking], rule: NotificationRule
    ):
        """Уведомление уборщиц (одна сущность 'смена' на всех, или каждому по копии)"""
        # Получаем всех уборщиц
        users_query = select(User).where(User.role == UserRole.CLEANER)
        result = await session.execute(users_query)
        cleaners = result.scalars().all()

        if not cleaners:
            logger.warning("No cleaners found.")
            return

        # Для уборщиц обычно формируется ОДНА сводка по всем домам
        count = 0
        for cleaner in cleaners:
            try:
                text = rule.message_func(bookings, cleaner)
                keyboard = (
                    rule.keyboard_func(bookings, cleaner)
                    if rule.keyboard_func
                    else None
                )

                await bot.send_message(
                    chat_id=cleaner.telegram_id, text=text, reply_markup=keyboard
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to notify cleaner {cleaner.telegram_id}: {e}")

        logger.info(f"Rule {rule.name}: Sent to {count} cleaners.")

    async def _notify_guests(
        self, session, bookings: List[Booking], rule: NotificationRule
    ):
        """Уведомление гостей (персонально каждому)"""
        import re

        # Получаем всех гостей (чтобы найти telegram_id по телефону)
        # Оптимизация: можно выбирать только тех, у кого есть телефон
        users_query = select(User).where(User.role == UserRole.GUEST)
        result = await session.execute(users_query)
        guest_users = result.scalars().all()

        # Создаем мапу {clean_phone: user}
        phone_user_map = {}
        for u in guest_users:
            if u.phone:
                # Нормализуем телефон из User
                p = re.sub(r"[\+\(\)\-\s]", "", u.phone)
                if p.startswith("8"):
                    p = "7" + p[1:]
                phone_user_map[p] = u

        count = 0
        for booking in bookings:
            # Нормализуем телефон из Booking
            b_phone = re.sub(r"[\+\(\)\-\s]", "", booking.guest_phone)
            if b_phone.startswith("8"):
                b_phone = "7" + b_phone[1:]

            # Попытка найти точное совпадение
            # Или частичное? Guest phone from Avito might be virtual.
            # Если это виртуальный номер, мы не сможем найти реального юзера, если он зашел под своим.
            # Но если он логинился, он шарил контакт. Мы сохранили ЕГО контакт.
            # Если в брони указан ТОТ ЖЕ номер, то найдем.

            target_user = None
            # 1. Пробуем точное
            if b_phone in phone_user_map:
                target_user = phone_user_map[b_phone]
            else:
                # 2. Пробуем найти "похожий" (вхождение)
                for p, u in phone_user_map.items():
                    if p in b_phone or b_phone in p:
                        target_user = u
                        break

            if target_user:
                try:
                    text = rule.message_func([booking], target_user)
                    keyboard = (
                        rule.keyboard_func([booking], target_user)
                        if rule.keyboard_func
                        else None
                    )

                    await bot.send_message(
                        chat_id=target_user.telegram_id,
                        text=text,
                        reply_markup=keyboard,
                    )
                    count += 1
                    logger.info(
                        f"Notified guest {target_user.name} ({target_user.telegram_id}) for booking {booking.id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to notify guest {target_user.telegram_id}: {e}"
                    )
            else:
                logger.debug(
                    f"Guest user not found for booking {booking.id} (phone {booking.guest_phone})"
                )

        logger.info(f"Rule {rule.name}: Sent to {count} guests.")

    async def _notify_admins(
        self, session, bookings: List[Booking], rule: NotificationRule
    ):
        """Уведомление админов"""
        users_query = select(User).where(User.role == UserRole.ADMIN)
        result = await session.execute(users_query)
        admins = result.scalars().all()
        from app.core.config import settings

        admin_ids = {u.telegram_id for u in admins}
        admin_ids.add(settings.telegram_chat_id)

        # Админам шлем сводку или по каждой броне? Обычно сводку.
        # Если нужно по каждой, нужно менять message_func.
        # Предполагаем сводку.

        count = 0
        for admin_id in admin_ids:
            try:
                text = rule.message_func(
                    bookings, None
                )  # None = нет персонализации получателя
                keyboard = (
                    rule.keyboard_func(bookings, None) if rule.keyboard_func else None
                )

                await bot.send_message(
                    chat_id=admin_id, text=text, reply_markup=keyboard
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        logger.info(f"Rule {rule.name}: Sent to {count} admins.")


# Global instance
notification_service = NotificationService()
