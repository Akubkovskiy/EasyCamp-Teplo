from datetime import date, timedelta
from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.models import House, HousePrice, HouseDiscount, Booking, BookingStatus


class PricingService:
    """Расчёт цен с учётом сезонности и скидок."""

    @staticmethod
    async def get_price_for_date(
        db: AsyncSession, house_id: int, target_date: date
    ) -> dict:
        """
        Возвращает цену за ночь для конкретной даты.
        Приоритет: сезонная цена > base_price.
        Поверх — скидка (если есть).
        """
        house = await db.get(House, house_id)
        if not house:
            return {"price": 0, "discount": 0, "final_price": 0, "label": None}

        # 1. Ищем сезонную цену
        stmt = select(HousePrice).where(
            and_(
                HousePrice.house_id == house_id,
                HousePrice.date_from <= target_date,
                HousePrice.date_to >= target_date,
            )
        )
        result = await db.execute(stmt)
        seasonal = result.scalar_one_or_none()

        base = seasonal.price_per_night if seasonal else house.base_price
        label = seasonal.label if seasonal else None

        # 2. Ищем скидку (для этого домика или глобальную)
        stmt = select(HouseDiscount).where(
            and_(
                HouseDiscount.is_active == True,
                HouseDiscount.date_from <= target_date,
                HouseDiscount.date_to >= target_date,
                (HouseDiscount.house_id == house_id) | (HouseDiscount.house_id.is_(None)),
            )
        ).order_by(HouseDiscount.discount_percent.desc())
        result = await db.execute(stmt)
        discount = result.scalars().first()

        discount_percent = discount.discount_percent if discount else 0
        discount_label = discount.label if discount else None
        final_price = int(base * (100 - discount_percent) / 100)

        return {
            "price": base,
            "discount_percent": discount_percent,
            "discount_label": discount_label,
            "final_price": final_price,
            "season_label": label,
        }

    @staticmethod
    async def calculate_stay_total(
        db: AsyncSession, house_id: int, check_in: date, check_out: date
    ) -> dict:
        """Расчёт стоимости за весь период проживания."""
        total = 0
        total_without_discount = 0
        nights = (check_out - check_in).days
        if nights <= 0:
            return {"total": 0, "nights": 0, "avg_per_night": 0}

        for i in range(nights):
            day = check_in + timedelta(days=i)
            info = await PricingService.get_price_for_date(db, house_id, day)
            total += info["final_price"]
            total_without_discount += info["price"]

        return {
            "total": total,
            "total_without_discount": total_without_discount,
            "nights": nights,
            "avg_per_night": total // nights,
        }

    @staticmethod
    async def get_display_price(db: AsyncSession, house_id: int) -> dict:
        """Цена для отображения в каталоге (на сегодня)."""
        return await PricingService.get_price_for_date(db, house_id, date.today())

    # --- CRUD for seasonal prices ---

    @staticmethod
    async def get_prices_for_house(
        db: AsyncSession, house_id: int
    ) -> list[HousePrice]:
        stmt = (
            select(HousePrice)
            .where(HousePrice.house_id == house_id)
            .order_by(HousePrice.date_from)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_price(
        db: AsyncSession, house_id: int, label: str,
        price_per_night: int, date_from: date, date_to: date,
    ) -> HousePrice:
        hp = HousePrice(
            house_id=house_id,
            label=label,
            price_per_night=price_per_night,
            date_from=date_from,
            date_to=date_to,
        )
        db.add(hp)
        await db.commit()
        await db.refresh(hp)
        return hp

    @staticmethod
    async def delete_price(db: AsyncSession, price_id: int) -> bool:
        stmt = delete(HousePrice).where(HousePrice.id == price_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    # --- CRUD for discounts ---

    @staticmethod
    async def get_active_discounts(
        db: AsyncSession, house_id: Optional[int] = None
    ) -> list[HouseDiscount]:
        conditions = [HouseDiscount.is_active == True]
        if house_id is not None:
            conditions.append(
                (HouseDiscount.house_id == house_id) | (HouseDiscount.house_id.is_(None))
            )
        stmt = (
            select(HouseDiscount)
            .where(and_(*conditions))
            .order_by(HouseDiscount.date_from)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_discount(
        db: AsyncSession, label: str, discount_percent: int,
        date_from: date, date_to: date,
        house_id: Optional[int] = None, is_auto: bool = False,
    ) -> HouseDiscount:
        d = HouseDiscount(
            house_id=house_id,
            label=label,
            discount_percent=discount_percent,
            date_from=date_from,
            date_to=date_to,
            is_auto=is_auto,
            is_active=True,
        )
        db.add(d)
        await db.commit()
        await db.refresh(d)
        return d

    @staticmethod
    async def deactivate_discount(db: AsyncSession, discount_id: int) -> bool:
        d = await db.get(HouseDiscount, discount_id)
        if not d:
            return False
        d.is_active = False
        await db.commit()
        return True

    # --- Auto-discount logic ---

    @staticmethod
    async def check_and_apply_auto_discounts(db: AsyncSession) -> list[dict]:
        """
        Проверяет загруженность на ближайшие дни.
        Если домик свободен завтра/послезавтра — создаёт горящую скидку.
        Возвращает список применённых скидок для уведомлений.
        """
        from app.services.house_service import HouseService

        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        hot_dates = [tomorrow, day_after]

        houses = await HouseService.get_all_houses(db)
        applied = []

        for house in houses:
            if house.base_price == 0:
                continue

            for target_date in hot_dates:
                # Проверяем, занят ли домик на эту дату
                stmt = select(Booking).where(
                    and_(
                        Booking.house_id == house.id,
                        Booking.check_in <= target_date,
                        Booking.check_out > target_date,
                        Booking.status.not_in([
                            BookingStatus.CANCELLED,
                        ]),
                    )
                )
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()

                if booking:
                    continue  # Занят — скидка не нужна

                # Проверяем, нет ли уже авто-скидки на эту дату
                stmt = select(HouseDiscount).where(
                    and_(
                        HouseDiscount.house_id == house.id,
                        HouseDiscount.is_auto == True,
                        HouseDiscount.is_active == True,
                        HouseDiscount.date_from <= target_date,
                        HouseDiscount.date_to >= target_date,
                    )
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    continue  # Уже есть авто-скидка

                # Скидка: % из настроек
                from app.core.config import settings
                days_ahead = (target_date - today).days
                percent = (
                    settings.auto_discount_tomorrow_percent
                    if days_ahead == 1
                    else settings.auto_discount_day_after_percent
                )

                discount = await PricingService.create_discount(
                    db=db,
                    label=f"Горящее: {target_date.strftime('%d.%m')}",
                    discount_percent=percent,
                    date_from=target_date,
                    date_to=target_date,
                    house_id=house.id,
                    is_auto=True,
                )
                applied.append({
                    "house": house.name,
                    "date": target_date,
                    "percent": percent,
                    "discount_id": discount.id,
                })

        return applied
