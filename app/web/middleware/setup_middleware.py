from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from fastapi import Request
from app.database import AsyncSessionLocal
from app.services.setup_service import SetupStateService

class SetupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 1. Allow static files (now under /admin-web/static)
        if path.startswith("/admin-web/static") or path == "/favicon.ico":
            return await call_next(request)

        # 2. Only intercept admin routes for now (others are API/Webhook)
        if not path.startswith("/admin-web"):
             return await call_next(request)

        # 3. Allowlist for specific Admin pages to prevent loops
        # Allow /setup, /login, /logout to function even if setup is not flagged
        if path.startswith("/admin-web/setup") or \
           path.startswith("/admin-web/login") or \
           path.startswith("/admin-web/logout"):
            return await call_next(request)

        # 4. Check Setup State
        # We need a fresh DB session here because Middleware is outside of Dependency injection
        async with AsyncSessionLocal() as db:
            is_done = await SetupStateService.is_initial_setup_done(db)
            
            if not is_done:
                # Redirect to Setup Wizard
                return RedirectResponse(url="/admin-web/setup", status_code=303)
        
        return await call_next(request)
