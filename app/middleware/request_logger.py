import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests timing and metadata.
    Logs: method, path, status_code, duration_ms, request_id
    Sampling: Only logs if duration > LOG_SLOW_REQUEST_THRESHOLD_MS
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        
        # Store for internal usage (services, loggers)
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)
            # Add to response headers for client/tracing
            response.headers["X-Request-ID"] = request_id
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log only if threshold exceeded (default 500ms)
            if duration_ms > settings.log_slow_request_threshold_ms:
                logger.info(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": round(duration_ms, 2),
                        "request_id": request_id,
                        # No body logging as requested
                    },
                )
        
        return response
