"""
Middleware для автоматической синхронизации с Google Sheets
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.services.sheets_service import sheets_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class AutoSyncMiddleware(BaseMiddleware):
    """
    Middleware для автоматической синхронизации при обращении к боту
    
    Синхронизация происходит с учетом кэширования (TTL),
    чтобы избежать превышения лимитов Google Sheets API
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработчик middleware
        
        Запускает синхронизацию перед обработкой сообщения,
        но только если прошло достаточно времени с последней синхронизации
        """
        
        # Trigger sync before handling the message (non-blocking)
        # sync_if_needed will check cache and skip if not needed
        if isinstance(event, (Message, CallbackQuery)):
            try:
                # Don't await - run in background to not delay message processing
                import asyncio
                # Use create_task to run in background
                # We need to import CallbackQuery if we haven't already
                from aiogram.types import CallbackQuery
                
                asyncio.create_task(sheets_service.sync_if_needed())
            except Exception as e:
                # Don't let sync errors break message handling
                logger.error(f"Auto-sync error: {e}")
        
        # Continue with message handling
        return await handler(event, data)
