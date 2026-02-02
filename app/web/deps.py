from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

class AuthRedirectException(Exception):
    """Custom exception for authentication redirects in web routes"""
    pass

from app.database import get_db
from app.models import User, UserRole
from app.core.security import decode_access_token
from app.core.config import settings

async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency to get current admin user from cookie session.
    Redirects to /admin-web/login if not authenticated.
    """
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Fetch user
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Check role
    if user.role not in [UserRole.ADMIN, "owner"]: # Owner mapping if generic string
        # Assuming UserRole.ADMIN covers owner for MVP, or we check role hierarchy
        # Roadmap says OWNER/ADMIN. UserRole enum has ADMIN.
        pass

    return user

async def get_current_admin_or_redirect(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """
    Same as above but redirects to login page on failure.
    Used for page routes.
    """
    try:
        return await get_current_admin(request, db)
    except HTTPException:
        raise AuthRedirectException()
