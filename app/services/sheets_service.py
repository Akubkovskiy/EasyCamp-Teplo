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
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
    
    def sync_bookings_to_sheet(self, bookings: List[Booking]):
        """Синхронизация броней в Google Sheets"""
        if not self.client:
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
        if not self.client:
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
        active_bookings = len([b for b in bookings if b.status.value in ['NEW', 'CONFIRMED', 'PAID']])
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


# Глобальный экземпляр сервиса
sheets_service = GoogleSheetsService()
