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
        if (
            settings.avito_client_id
            and settings.avito_item_ids
            and settings.avito_sync_interval_minutes > 0
        ):
            self.scheduler.add_job(
                sync_avito_job,
                IntervalTrigger(minutes=settings.avito_sync_interval_minutes),
                id="avito_sync",
                name="Sync Avito bookings",
                replace_existing=True,
            )
            logger.info(
                f"Registered Avito sync job (every {settings.avito_sync_interval_minutes} minutes)"
            )
        else:
            if settings.avito_sync_interval_minutes == 0:
                logger.info("Avito sync disabled (interval = 0)")
            else:
                logger.warning(
                    "Avito sync job not registered - missing credentials or item IDs"
                )

        # Google Sheets sync - каждые N минут
        if (
            settings.google_sheets_spreadsheet_id
            and settings.sheets_sync_interval_minutes > 0
        ):
            self.scheduler.add_job(
                sync_sheets_job,
                IntervalTrigger(minutes=settings.sheets_sync_interval_minutes),
                id="sheets_sync",
                name="Sync Google Sheets",
                replace_existing=True,
            )
            logger.info(
                f"Registered Sheets sync job (every {settings.sheets_sync_interval_minutes} minutes)"
            )
        else:
            if settings.sheets_sync_interval_minutes == 0:
                logger.info("Sheets sync disabled (interval = 0)")
            else:
                logger.warning(
                    "Sheets sync job not registered - missing spreadsheet ID"
                )

        # Cleaner notifications (Cron)
        from app.jobs.cleaning_notifier import check_and_notify_cleaners
        from apscheduler.triggers.cron import CronTrigger

        try:
            time_str = settings.cleaning_notification_time  # "HH:MM"
            parts = time_str.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])

                self.scheduler.add_job(
                    check_and_notify_cleaners,
                    CronTrigger(hour=hour, minute=minute),
                    id="cleaner_notify",
                    name="Notify cleaners",
                    replace_existing=True,
                )
                logger.info(f"Registered cleaner notification job (at {time_str})")
            else:
                logger.error(f"Invalid cleaning_notification_time format: {time_str}")

            # Guest notifications (Fixed time for now: 10:00)
            from app.jobs.guest_notifier import check_and_notify_guests

            self.scheduler.add_job(
                check_and_notify_guests,
                CronTrigger(hour=10, minute=0),
                id="guest_notify",
                name="Notify guests",
                replace_existing=True,
            )
            logger.info("Registered guest notification job (at 10:00)")

            # Status updater - daily at 00:01
            from app.jobs.status_updater_job import update_booking_statuses_job

            self.scheduler.add_job(
                update_booking_statuses_job,
                CronTrigger(hour=0, minute=1),
                id="status_updater",
                name="Update booking statuses",
                replace_existing=True,
            )
            logger.info("Registered status updater job (at 00:01)")

            # Database Backup - daily at 03:00
            from app.services.backup_service import backup_database_to_drive

            self.scheduler.add_job(
                backup_database_to_drive,
                CronTrigger(hour=3, minute=0),
                id="db_backup",
                name="Backup database to Drive",
                replace_existing=True,
            )
            logger.info("Registered database backup job (at 03:00)")

        except Exception as e:
            logger.error(f"Failed to register notification jobs: {e}")

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

    def reload(self):
        """Перезагрузка всех задач (для обновления настроек)"""
        if self.scheduler.running:
            self.scheduler.remove_all_jobs()
            self._jobs_registered = False
            self.register_jobs()
            logger.info("Scheduler jobs reloaded")


# Глобальный экземпляр
scheduler_service = SchedulerService()
