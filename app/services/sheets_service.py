"""
Сервис для работы с Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
from typing import List

from app.core.config import settings
from app.models import Booking, House


class GoogleSheetsService:
    """Сервис для синхронизации данных с Google Sheets"""
    
    def __init__(self):
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self.credentials_file = settings.google_sheets_credentials_file
        self.client = None
        self.spreadsheet = None
        
        # Sync caching to prevent excessive API calls
        self._last_sync_time = None
        self._sync_cache_ttl_seconds = getattr(settings, 'sync_cache_ttl_seconds', 30)
        self._is_syncing = False  # Prevent concurrent syncs
    
    def connect(self):
        """Подключение к Google Sheets"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            self.credentials_file,
            scopes=scopes
        )
        
        self.client = gspread.authorize(creds)
        try:
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception:
            self.client = None  # Сбрасываем клиент при ошибке открытия таблицы
            raise
    
    def sync_bookings_to_sheet(self, bookings: List[Booking]):
        """Синхронизация броней в Google Sheets"""
        if not self.client or not self.spreadsheet:
            self.connect()
        
        # Получаем или создаем лист "Все брони"
        try:
            worksheet = self.spreadsheet.worksheet("Все брони")
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title="Все брони",
                rows=1000,
                cols=11
            )
        
        # Очищаем лист
        worksheet.clear()
        
        # Заголовки
        headers = [
            "ID",
            "Дата заезда",
            "Дата выезда",
            "Гость",
            "Телефон",
            "Домик",
            "Гостей",
            "Цена",
            "Статус",
            "Источник",
            "Создано"
        ]
        
        # Формируем данные
        data = [headers]
        
        for booking in bookings:
            row = [
                booking.id,
                booking.check_in.strftime("%d.%m.%Y"),
                booking.check_out.strftime("%d.%m.%Y"),
                booking.guest_name,
                booking.guest_phone,
                booking.house.name,
                booking.guests_count,
                float(booking.total_price),
                booking.status.value,
                booking.source.value,
                booking.created_at.strftime("%d.%m.%Y %H:%M")
            ]
            data.append(row)
        
        # Записываем данные
        if len(data) > 0:
            # Используем batch_update для записи всех данных сразу
            worksheet.batch_update([{
                'range': f'A1:K{len(data)}',
                'values': data
            }])
        
        # Форматирование
        self._format_bookings_sheet(worksheet)
    
    def _format_bookings_sheet(self, worksheet):
        """Форматирование листа с бронями"""
        # Жирный шрифт для заголовков
        worksheet.format('A1:K1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Автоширина колонок
        worksheet.columns_auto_resize(0, 10)
    
    def create_dashboard(self, bookings: List[Booking]):
        """Создание Dashboard с общей статистикой"""
        if not self.client or not self.spreadsheet:
            self.connect()
        
        try:
            worksheet = self.spreadsheet.worksheet("Dashboard")
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title="Dashboard",
                rows=50,
                cols=10
            )
        
        worksheet.clear()
        
        # Заголовок
        worksheet.update_acell('A1', 'TEPLO АРХЫЗ - УПРАВЛЕНИЕ БРОНЯМИ')
        worksheet.format('A1', {
            'textFormat': {'bold': True, 'fontSize': 16},
            'horizontalAlignment': 'CENTER'
        })
        
        # Дата обновления
        today = date.today().strftime("%d.%m.%Y")
        worksheet.update_acell('A2', f'Обновлено: {today}')
        
        # Статистика
        worksheet.update_acell('A4', 'СТАТИСТИКА')
        worksheet.format('A4', {'textFormat': {'bold': True, 'fontSize': 14}})
        
        # Подсчет статистики
        total_bookings = len(bookings)
        active_bookings = len([b for b in bookings if b.status.value in ['new', 'confirmed', 'paid', 'active']])
        total_revenue = sum(b.total_price for b in bookings)
        
        stats_data = [
            ['Всего броней:', total_bookings],
            ['Активных:', active_bookings],
            ['Общий доход:', f'{total_revenue:,.0f} ₽']
        ]
        
        worksheet.batch_update([{
            'range': 'A5:B7',
            'values': stats_data
        }])
    
    async def sync_bookings_async(self, bookings: List[Booking]):
        """Async wrapper для синхронизации броней"""
        import asyncio
        from datetime import datetime
        
        # Prevent concurrent syncs
        if self._is_syncing:
            return False
        
        try:
            self._is_syncing = True
            
            # Run sync in thread pool to avoid blocking
            await asyncio.to_thread(self.sync_bookings_to_sheet, bookings)
            await asyncio.to_thread(self.create_dashboard, bookings)
            
            self._last_sync_time = datetime.now()
            return True
            
        finally:
            self._is_syncing = False
    
    async def sync_if_needed(self, force: bool = False) -> bool:
        """
        Умная синхронизация - только если прошло достаточно времени
        
        Args:
            force: Принудительная синхронизация игнорируя кэш
            
        Returns:
            True если синхронизация выполнена, False если пропущена
        """
        import asyncio
        import logging
        from datetime import datetime, timedelta
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        
        logger = logging.getLogger(__name__)
        
        # Check if sync is needed
        if not force and self._last_sync_time:
            time_since_last_sync = (datetime.now() - self._last_sync_time).total_seconds()
            if time_since_last_sync < self._sync_cache_ttl_seconds:
                logger.debug(f"Skipping sync - last sync was {time_since_last_sync:.1f}s ago (TTL: {self._sync_cache_ttl_seconds}s)")
                return False
        
        # Already syncing
        if self._is_syncing:
            logger.debug("Sync already in progress, skipping")
            return False
        
        try:
            # Get bookings from database
            from app.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in)
                result = await session.execute(stmt)
                bookings = result.scalars().all()
            
            if not bookings:
                logger.debug("No bookings to sync")
                return False
            
            # Perform sync
            logger.info(f"📊 Syncing {len(bookings)} bookings to Google Sheets...")
            success = await self.sync_bookings_async(bookings)
            
            if success:
                logger.info(f"✅ Successfully synced {len(bookings)} bookings")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}", exc_info=True)
            return False


# Глобальный экземпляр сервиса
sheets_service = GoogleSheetsService()

