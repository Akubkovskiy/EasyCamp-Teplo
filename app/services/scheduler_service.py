"""
Сервис планировщика для автоматической синхронизации
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Сервис для управления периодическими задачами"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs_registered = False
    
    def register_jobs(self):
        """Регистрация всех периодических задач"""
        if self._jobs_registered:
            logger.warning("Jobs already registered")
            return
        
        if not settings.enable_auto_sync:
            logger.info("Auto-sync is disabled in settings")
            return
        
        # Импортируем здесь чтобы избежать циклических зависимостей
        from app.jobs.avito_sync_job import sync_avito_job
        from app.jobs.sheets_sync_job import sync_sheets_job
        
        # Avito sync - каждые N минут
        if settings.avito_client_id and settings.avito_item_ids and settings.avito_sync_interval_minutes > 0:
            self.scheduler.add_job(
                sync_avito_job,
                IntervalTrigger(minutes=settings.avito_sync_interval_minutes),
                id='avito_sync',
                name='Sync Avito bookings',
                replace_existing=True
            )
            logger.info(f"Registered Avito sync job (every {settings.avito_sync_interval_minutes} minutes)")
        else:
            if settings.avito_sync_interval_minutes == 0:
                logger.info("Avito sync disabled (interval = 0)")
            else:
                logger.warning("Avito sync job not registered - missing credentials or item IDs")
        
        # Google Sheets sync - каждые N минут
        if settings.google_sheets_spreadsheet_id and settings.sheets_sync_interval_minutes > 0:
            self.scheduler.add_job(
                sync_sheets_job,
                IntervalTrigger(minutes=settings.sheets_sync_interval_minutes),
                id='sheets_sync',
                name='Sync Google Sheets',
                replace_existing=True
            )
            logger.info(f"Registered Sheets sync job (every {settings.sheets_sync_interval_minutes} minutes)")
        else:
            if settings.sheets_sync_interval_minutes == 0:
                logger.info("Sheets sync disabled (interval = 0)")
            else:
                logger.warning("Sheets sync job not registered - missing spreadsheet ID")
        
        self._jobs_registered = True
    
    def start(self):
        """Запуск планировщика"""
        if not self.scheduler.running:
            self.register_jobs()
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler already running")
    
    def shutdown(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def pause(self):
        """Приостановка всех задач"""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume(self):
        """Возобновление всех задач"""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
    
    def get_jobs(self):
        """Получить список всех задач"""
        return self.scheduler.get_jobs()


# Глобальный экземпляр
scheduler_service = SchedulerService()
