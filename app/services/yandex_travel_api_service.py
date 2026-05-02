"""
Клиент Яндекс Путешествий White Label Partner API.

Документация: https://yandex.ru/dev/travel-partners-api/doc/ru/
Базовый URL:   https://whitelabel.travel.yandex-net.ru/

Аутентификация: OAuth-токен (срок действия 1 год).
  Заголовок: Authorization: OAuth <token>
  Токен не обновляется автоматически — хранится в YANDEX_TRAVEL_OAUTH_TOKEN.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://whitelabel.travel.yandex-net.ru"
# Пока White Label доступ не подтверждён — все запросы вернут 401.
# После подтверждения (24 ч) здесь нужно уточнить точные пути к
# endpoint'ам property management: calendar / prices / orders.


class YandexTravelAPIService:
    """HTTP-клиент для Яндекс Путешествий Partner API."""

    def __init__(self) -> None:
        self.oauth_token: str = settings.yandex_travel_oauth_token

    # ------------------------------------------------------------------
    # Внутренние хелперы
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"OAuth {self.oauth_token}",
            "User-Agent": f"{settings.project_name}/1.0",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: Optional[Dict] = None, timeout: int = 10) -> Any:
        url = f"{BASE_URL}{path}"
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            if resp.status_code == 401:
                logger.error("YaTr 401: проверьте YANDEX_TRAVEL_OAUTH_TOKEN и White Label статус")
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error("YaTr GET %s → HTTP %s: %s", path, e.response.status_code if e.response else "?", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("YaTr GET %s → %s", path, e)
            return None

    def _post(self, path: str, body: Dict, timeout: int = 15) -> Any:
        url = f"{BASE_URL}{path}"
        try:
            resp = requests.post(url, headers=self._headers(), json=body, timeout=timeout)
            if resp.status_code == 401:
                logger.error("YaTr 401: проверьте YANDEX_TRAVEL_OAUTH_TOKEN и White Label статус")
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error("YaTr POST %s → HTTP %s: %s", path, e.response.status_code if e.response else "?", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("YaTr POST %s → %s", path, e)
            return None

    # ------------------------------------------------------------------
    # Проверка доступа
    # ------------------------------------------------------------------

    def check_access(self) -> bool:
        """
        Тестовый запрос — проверка токена и White Label статуса.
        TODO: уточнить endpoint после получения доступа.
        """
        data = self._get("/hotels/hotel/", params={"hotel_id": "1019057204"})
        if data is not None:
            logger.info("YaTr: доступ подтверждён")
            return True
        logger.warning("YaTr: доступ недоступен (ожидание White Label активации?)")
        return False

    # ------------------------------------------------------------------
    # Отели / объекты
    # ------------------------------------------------------------------

    def get_hotel(self, hotel_id: str) -> Optional[Dict]:
        """Информация об отеле/объекте по hotel_id."""
        return self._get("/hotels/hotel/", params={"hotel_id": hotel_id})

    # ------------------------------------------------------------------
    # Брони / заказы
    # ------------------------------------------------------------------

    def get_orders_by_date_range(
        self,
        date_from: date,
        date_to: date,
    ) -> List[Dict]:
        """
        Получить список заказов за период (по дате создания).

        TODO: уточнить точный endpoint и формат ответа после активации White Label.
              Предположительно: GET /orders/report или GET /partners/orders
        """
        # --- PLACEHOLDER: endpoint требует уточнения ---
        # Согласно документации, доступны три вида отчётов:
        # - по дате создания
        # - по последней модификации
        # - по дате загрузки в billing
        # Используем последнюю модификацию для надёжного polling.
        data = self._get(
            "/orders/report",
            params={
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "type": "by_modification",
            },
        )
        if data is None:
            return []
        # Ожидаем список в поле "orders" или root-массив
        if isinstance(data, list):
            return data
        return data.get("orders", [])

    def get_orders_modified_since(self, since: datetime) -> List[Dict]:
        """
        Polling-метод: заказы, изменившиеся с момента since.
        Используется в sync job для минимизации трафика.
        """
        return self.get_orders_by_date_range(
            date_from=since.date(),
            date_to=(datetime.utcnow() + timedelta(days=1)).date(),
        )

    def get_order(self, order_id: str) -> Optional[Dict]:
        """Детали одного заказа. TODO: уточнить endpoint."""
        return self._get(f"/orders/{order_id}")

    # ------------------------------------------------------------------
    # Управление календарём (доступность)
    # ------------------------------------------------------------------

    def update_availability(
        self,
        hotel_id: str,
        room_id: str,
        date_from: date,
        date_to: date,
        available: bool,
    ) -> bool:
        """
        Обновить доступность номера/домика на диапазон дат.

        TODO: endpoint требует уточнения после активации White Label.
              Предположительный путь: /hotels/{hotel_id}/rooms/{room_id}/availability
        """
        body = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "available": available,
        }
        result = self._post(
            f"/hotels/{hotel_id}/rooms/{room_id}/availability",
            body=body,
        )
        if result is not None:
            logger.info(
                "YaTr: availability %s → %s/%s %s–%s",
                "open" if available else "closed",
                hotel_id, room_id, date_from, date_to,
            )
            return True
        logger.warning("YaTr: не удалось обновить доступность %s/%s", hotel_id, room_id)
        return False

    def close_dates_from_local_bookings(
        self,
        hotel_id: str,
        room_id: str,
        local_bookings: List[Any],
        days_forward: int = 180,
    ) -> bool:
        """
        Закрыть даты в Яндекс Путешествиях на основе локальных броней.

        Логика: итерируемся по локальным бронями, закрываем занятые диапазоны.
        Не трогаем брони с source=YANDEX_TRAVEL (они уже видны платформе).
        """
        from app.models import BookingStatus, BookingSource

        today = date.today()
        end_date = today + timedelta(days=days_forward)
        success = True

        for booking in local_bookings:
            if booking.status in (BookingStatus.CANCELLED, BookingStatus.COMPLETED):
                continue
            if hasattr(booking, "source") and booking.source == BookingSource.YANDEX_TRAVEL:
                continue  # Не синкаем Яндекс-брони обратно в Яндекс

            check_in = booking.check_in
            check_out = booking.check_out
            if isinstance(check_in, datetime):
                check_in = check_in.date()
            if isinstance(check_out, datetime):
                check_out = check_out.date()

            if check_out <= today or check_in >= end_date:
                continue  # Вне окна

            ok = self.update_availability(
                hotel_id=hotel_id,
                room_id=room_id,
                date_from=check_in,
                date_to=check_out,
                available=False,
            )
            if not ok:
                success = False

        return success

    # ------------------------------------------------------------------
    # Цены
    # ------------------------------------------------------------------

    def update_prices(
        self,
        hotel_id: str,
        room_id: str,
        price_entries: List[Dict],
    ) -> bool:
        """
        Обновить цены для номера/домика.

        price_entries: [{"date": "2026-05-10", "price": 5500}, ...]

        TODO: endpoint требует уточнения после активации White Label.
              Предположительный путь: /hotels/{hotel_id}/rooms/{room_id}/prices
        """
        body = {"prices": price_entries}
        result = self._post(
            f"/hotels/{hotel_id}/rooms/{room_id}/prices",
            body=body,
        )
        if result is not None:
            logger.info(
                "YaTr: prices updated %s/%s — %d entries",
                hotel_id, room_id, len(price_entries),
            )
            return True
        logger.warning("YaTr: не удалось обновить цены %s/%s", hotel_id, room_id)
        return False


# Глобальный синглтон
yandex_travel_api_service = YandexTravelAPIService()
