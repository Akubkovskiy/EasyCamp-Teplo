from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.web.deps import get_current_admin_or_redirect
from app.services.settings_service import SettingsService
from app.web.help_texts import HELP_TEXTS

templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web/settings", tags=["web-settings"])

@router.get("/", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Страница редактирования настроек"""
    # Get current DB settings
    current_settings = await SettingsService.get_project_settings(db)
    # Also fetch all raw settings to pre-fill specific fields
    all_raw = await SettingsService.get_all_settings(db)
    
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "project_name": current_settings.get("name"), # For header
            "settings": all_raw, # For form fields
            "help_texts": HELP_TEXTS,
            "user": user,
            "success": request.query_params.get("success")
        }
    )

@router.post("/", response_class=HTMLResponse)
async def settings_save(
    request: Request,
    project_name: str = Form(...),
    project_location: str = Form(...),
    contact_phone: str = Form(...),
    project_address: str = Form(""),
    contact_admin: str = Form(""),
    ai_enabled: str = Form(...),
    spreadsheet_id: str = Form(""),
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Сохранение настроек"""
    from app.models import GlobalSetting
    from sqlalchemy import select

    async def save_setting(key, val):
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        res = await db.execute(stmt)
        obj = res.scalar_one_or_none()
        if not obj:
            db.add(GlobalSetting(key=key, value=val))
        else:
            obj.value = val

    await save_setting("project_name", project_name)
    await save_setting("project_location", project_location)
    await save_setting("contact_phone", contact_phone)
    await save_setting("project_address", project_address)
    await save_setting("contact_admin_username", contact_admin)
    
    await save_setting("ai_enabled", ai_enabled)
    await save_setting("google_sheets_spreadsheet_id", spreadsheet_id)
    
    await db.commit()

    return RedirectResponse(
        url="/admin-web/settings?success=1", 
        status_code=status.HTTP_303_SEE_OTHER
    )
