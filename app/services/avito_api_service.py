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
                    "date_end": date_end
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
        days_forward: int = 90
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


# Глобальный экземпляр сервиса
avito_api_service = AvitoAPIService()
