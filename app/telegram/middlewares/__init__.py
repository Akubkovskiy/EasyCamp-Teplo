"""
Telegram bot middlewares
"""

from .sync_middleware import AutoSyncMiddleware

__all__ = ["AutoSyncMiddleware"]
