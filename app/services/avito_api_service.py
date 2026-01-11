"""
Сервис для работы с Avito API
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AvitoAPIService:
    """Сервис для работы с Avito API краткосрочной аренды"""
    
    BASE_URL = "https://api.avito.ru"
    
    def __init__(self):
        self.client_id = settings.avito_client_id
        self.client_secret = settings.avito_client_secret
        self.user_id = settings.avito_user_id
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def get_access_token(self) -> str:
        """Получение access token через client_credentials"""
        logger.info("Requesting Avito access token...")
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "short_term_rent:read short_term_rent:write"
                },
                timeout=10
            )
            
            # Логируем статус и тело ответа
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем наличие access_token
            if 'access_token' not in data:
                logger.error(f"No access_token in response: {data}")
                raise ValueError(f"Avito API returned unexpected response: {data}")
            
            self.access_token = data['access_token']
            
            # Токен действует 24 часа, сохраняем время истечения
            expires_in = data.get('expires_in', 86400)  # По умолчанию 24 часа
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info(f"Access token obtained, expires at {self.token_expires_at}")
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    def ensure_token(self):
        """Проверка и обновление токена при необходимости"""
        if not self.access_token or not self.token_expires_at:
            self.get_access_token()
        elif datetime.now() >= self.token_expires_at:
            logger.info("Token expired, refreshing...")
            self.get_access_token()
    
    def get_bookings(
        self, 
        item_id: int, 
        date_start: str, 
        date_end: str
    ) -> Dict:
        """
        Получение списка броней по объявлению
        
        Args:
            item_id: ID объявления на Avito
            date_start: Дата начала выборки (формат: YYYY-MM-DD)
            date_end: Дата окончания выборки (формат: YYYY-MM-DD)
            
        Returns:
            Dict с ключом 'bookings' содержащим список броней
        """
        self.ensure_token()
        
        logger.info(f"Fetching bookings for item {item_id} from {date_start} to {date_end}")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/realty/v1/accounts/{self.user_id}/items/{item_id}/bookings",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "date_start": date_start,
                    "date_end": date_end,
                    "with_unpaid": "true"
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Received {len(data.get('bookings', []))} bookings")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch bookings: {e}")
            raise
    
    def get_bookings_for_period(
        self, 
        item_id: int, 
        days_forward: int = 180
    ) -> List[Dict]:
        """
        Получение броней за период (от сегодня вперед)
        
        Args:
            item_id: ID объявления
            days_forward: Сколько дней вперед от сегодня
            
        Returns:
            Список броней
        """
        today = datetime.now().date()
        end_date = today + timedelta(days=days_forward)
        
        data = self.get_bookings(
            item_id=item_id,
            date_start=today.isoformat(),
            date_end=end_date.isoformat()
        )
        
        return data.get('bookings', [])
    
    def get_all_bookings(self, item_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Получение броней для всех объявлений
        
        Args:
            item_ids: Список ID объявлений
            
        Returns:
            Словарь {item_id: [bookings]}
        """
        result = {}
        
        for item_id in item_ids:
            try:
                bookings = self.get_bookings_for_period(item_id)
                result[item_id] = bookings
            except Exception as e:
                logger.error(f"Failed to fetch bookings for item {item_id}: {e}")
                result[item_id] = []
        
        return result
    
    def block_dates(
        self,
        item_id: int,
        check_in: str,
        check_out: str,
        comment: str = None
    ) -> bool:
        """
        Блокировка дат в календаре Avito
        
        Args:
            item_id: ID объявления на Avito
            check_in: Дата заезда (формат: YYYY-MM-DD)
            check_out: Дата выезда (формат: YYYY-MM-DD)
            comment: Комментарий к брони (опционально)
            
        Returns:
            True если блокировка успешна, False в случае ошибки
            
        Note:
            Последний день (check_out) доступен для пользователя (open end).
            Бронь на 1 день = промежуток в 2 дня.
        """
        self.ensure_token()
        
        logger.info(f"Blocking dates for item {item_id}: {check_in} to {check_out}")
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/core/v1/accounts/{self.user_id}/items/{item_id}/bookings",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "bookings": [
                        {
                            "date_start": check_in,
                            "date_end": check_out,
                            "type": "manual",
                            "comment": comment or "Забронировано через EasyCamp Bot"
                        }
                    ],
                    "source": "EasyCamp"
                },
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Dates blocked successfully for item {item_id}")
            return True
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            
            if status_code == 409:
                logger.warning(f"⚠️ Conflict: Dates overlap with existing paid booking on Avito")
            elif status_code == 403:
                logger.error(f"❌ Forbidden: User doesn't own item {item_id}")
            elif status_code == 404:
                logger.error(f"❌ Not found: Item {item_id} not found")
            else:
                logger.error(f"❌ HTTP error blocking dates: {e}")
            
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to block dates: {e}")
            return False
    
    def unblock_dates(
        self,
        item_id: int,
        check_in: str,
        check_out: str
    ) -> bool:
        """
        Разблокировка дат в календаре Avito через обновление интервалов доступности
        
        Args:
            item_id: ID объявления на Avito
            check_in: Дата заезда отмененной брони (формат: YYYY-MM-DD)
            check_out: Дата выезда отмененной брони (формат: YYYY-MM-DD)
            
        Returns:
            True если разблокировка успешна, False в случае ошибки
            
        Note:
            Использует правильный алгоритм:
            1. Получает все текущие брони
            2. Вычисляет свободные интервалы между ними
            3. Отправляет свободные интервалы через /intervals API
        """
        self.ensure_token()
        
        logger.info(f"Unblocking dates for item {item_id}: {check_in} to {check_out}")
        
        try:
            from app.core.config import settings
            from datetime import datetime, timedelta
            
            # Шаг 1: Получаем все текущие брони для этого item_id
            today = datetime.now().date()
            end_date = today + timedelta(days=settings.booking_window_days)
            
            logger.info(f"Fetching bookings for item {item_id} from {today} to {end_date}")
            
            bookings_data = self.get_bookings(
                item_id=item_id,
                date_start=today.isoformat(),
                date_end=end_date.isoformat()
            )
            
            bookings = bookings_data.get('bookings', [])
            logger.info(f"Found {len(bookings)} existing bookings")
            
            # Шаг 2: Фильтруем брони, исключая отмененную
            # Преобразуем даты в объекты date для сравнения
            cancelled_start = datetime.fromisoformat(check_in).date()
            cancelled_end = datetime.fromisoformat(check_out).date()
            
            remaining_bookings = []
            for booking in bookings:
                booking_start = datetime.fromisoformat(booking['date_start']).date()
                booking_end = datetime.fromisoformat(booking['date_end']).date()
                
                # Пропускаем отмененную бронь
                if booking_start == cancelled_start and booking_end == cancelled_end:
                    logger.info(f"Skipping cancelled booking: {booking['date_start']} to {booking['date_end']}")
                    continue
                
                remaining_bookings.append({
                    'start': booking_start,
                    'end': booking_end
                })
            
            logger.info(f"Remaining bookings after cancellation: {len(remaining_bookings)}")
            
            # Шаг 3: Сортируем брони по дате начала
            remaining_bookings.sort(key=lambda x: x['start'])
            
            # Шаг 4: Вычисляем свободные интервалы
            free_intervals = []
            current_date = today
            
            for booking in remaining_bookings:
                # Если есть промежуток между current_date и началом брони
                if current_date < booking['start']:
                    free_intervals.append({
                        'date_start': current_date.isoformat(),
                        'date_end': booking['start'].isoformat(),
                        'open': 1
                    })
                # Сдвигаем current_date на конец текущей брони
                if booking['end'] > current_date:
                    current_date = booking['end']
            
            # Добавляем последний интервал до конца окна бронирования
            if current_date < end_date:
                free_intervals.append({
                    'date_start': current_date.isoformat(),
                    'date_end': end_date.isoformat(),
                    'open': 1
                })
            
            logger.info(f"Calculated {len(free_intervals)} free intervals")
            
            # Шаг 5: Отправляем обновленные интервалы через /intervals API
            response = requests.post(
                f"{self.BASE_URL}/realty/v1/items/intervals",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "intervals": free_intervals,
                    "item_id": item_id,
                    "source": "EasyCamp"
                },
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Dates unblocked successfully for item {item_id}")
            return True
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.error(f"❌ HTTP error unblocking dates (status {status_code}): {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to unblock dates: {e}", exc_info=True)
            return False


# Глобальный экземпляр сервиса
avito_api_service = AvitoAPIService()
