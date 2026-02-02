from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.web.deps import get_current_admin_or_redirect
from app.models import User

templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web", tags=["web-dashboard"])

from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.settings_service import SettingsService

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Главная страница админки (защищена)"""
    project_settings = await SettingsService.get_project_settings(db)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "project_name": project_settings.get("name") or settings.project_name,
            "user": user
        }
    )
