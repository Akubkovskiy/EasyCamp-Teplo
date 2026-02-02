"""
Rate limiter configuration module.

Separated to avoid circular imports between main.py and webhook.py.
Import `limiter` from here to use the @limiter.limit() decorator.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Create limiter instance
# - key_func: Uses client IP for rate limiting
# - enabled: Killswitch via RATE_LIMIT_ENABLED env var
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
)
