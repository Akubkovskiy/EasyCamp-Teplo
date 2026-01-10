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
    
    
    def _format_bookings_sheet(self, worksheet):
        """Форматирование листа с бронями"""
        # Жирный шрифт для заголовков
        worksheet.format('A1:N1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Автоширина колонок
        worksheet.columns_auto_resize(0, 13)
        
        # Выпадающий список для статусов (Column L / 12th column)
        # Updated statuses based on user request
        status_options = ["Ожидает оплаты", "Ждёт заселения", "Оплата внесена", "Отменена", "Завершена"]
        
        validation_rule = {
            'condition': {
                'type': 'ONE_OF_LIST',
                'values': [{'userEnteredValue': v} for v in status_options]
            },
            'showCustomUi': True,
            'strict': True
        }
        
        # Apply validation to the whole Status column starting from row 2
        # Column L is index 11 (0-based)
        requests = [{
            'setDataValidation': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': 1,  # Skip header
                    'endRowIndex': 1000,
                    'startColumnIndex': 11,
                    'endColumnIndex': 12
                },
                'rule': validation_rule
            }
        }]
        
        self.spreadsheet.batch_update({'requests': requests})

    def sync_bookings_to_sheet(self, bookings: List[Booking]):
        """Синхронизация броней в Google Sheets"""
        if not self.client or not self.spreadsheet:
            self.connect()
        
        # Mappings for localization
        status_map = {
            'new': 'Ожидает оплаты',
            'confirmed': 'Ждёт заселения',
            'paid': 'Оплата внесена',
            'cancelled': 'Отменена',
            'completed': 'Завершена'
        }
        
        source_map = {
            'avito': 'Авито',
            'telegram': 'Телеграм',
            'direct': 'Прямая',
            'other': 'Другое'
        }
        
        # Получаем или создаем лист "Все брони"
        try:
            worksheet = self.spreadsheet.worksheet("Все брони")
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title="Все брони",
                rows=1000,
                cols=14
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
            "Предоплата (моя)",
            "Остаток",
            "Комиссия",
            "Статус",
            "Источник",
            "Создано"
        ]
        
        # Формируем данные
        data = [headers]
        
        for i, booking in enumerate(bookings, start=2):
            # Calculate values
            total_price = float(booking.total_price)
            # Use direct fields from DB
            advance_total = float(booking.advance_amount or 0)
            commission = float(booking.commission or 0)
            
            # Use direct owner amount if available (Avito), or fallback to total (Direct bookings)
            if booking.prepayment_owner and float(booking.prepayment_owner) > 0:
                advance_user_share = float(booking.prepayment_owner)
            elif booking.source == 'avito' and commission > 0:
                 # Fallback if field wasn't populated yet but we have commission
                 advance_user_share = advance_total - commission
            else:
                 # For direct/other bookings, advance is fully user's
                 advance_user_share = advance_total
            
            # Localize values
            status_rus = status_map.get(booking.status.value, booking.status.value)
            source_rus = source_map.get(booking.source.value, booking.source.value)
            
            row = [
                booking.id,
                booking.check_in.strftime("%d.%m.%Y"),
                booking.check_out.strftime("%d.%m.%Y"),
                booking.guest_name,
                f"'{booking.guest_phone}" if booking.guest_phone else "", # Force text format
                booking.house.name,
                booking.guests_count,
                total_price,
                advance_user_share,
                f'=H{i}-I{i}-K{i} ',  # Remain formula: Total - OwnerAdvance - Commission
                commission,
                status_rus,
                source_rus,
                booking.created_at.strftime("%d.%m.%Y %H:%M")
            ]
            data.append(row)
        
        # Записываем данные
        if len(data) > 0:
            # Используем batch_update для записи всех данных сразу
            # Используем update для записи данных
            worksheet.batch_update([{
                'range': f'A1:N{len(data)}',
                'values': data
            }], value_input_option='USER_ENTERED')
        
        # Форматирование
        self._format_bookings_sheet(worksheet)
    
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
        from datetime import datetime
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        worksheet.update_acell('A2', f'Обновлено: {now}')
        
        # Статистика
        worksheet.update_acell('A4', 'СТАТИСТИКА')
        worksheet.format('A4', {'textFormat': {'bold': True, 'fontSize': 14}})
        
        # Подсчет статистики
        total_bookings = len(bookings)
        
        # Filter for active bookings (excluding cancelled)
        active_statuses = ['new', 'confirmed', 'paid', 'active']
        active_list = [b for b in bookings if b.status.value in active_statuses]
        
        active_bookings_count = len(active_list)
        
        # Revenue should be sum of active bookings only (Total Price = Advance + Remainder)
        total_revenue = sum(b.total_price for b in active_list)
        
        stats_data = [
            ['Всего броней:', total_bookings],
            ['Активных:', active_bookings_count],
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

