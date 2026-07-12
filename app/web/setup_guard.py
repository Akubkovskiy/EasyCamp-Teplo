from fastapi import HTTPException, status

from app.database import AsyncSessionLocal
from app.services.setup_service import SetupStateService


async def require_setup_open() -> None:
    """Make the bootstrap surface unreachable after initial setup completes."""
    async with AsyncSessionLocal() as db:
        if await SetupStateService.is_initial_setup_done(db):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
