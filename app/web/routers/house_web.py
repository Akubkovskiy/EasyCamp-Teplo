from fastapi import APIRouter, Request, Depends, Form, status, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models import User
from app.web.deps import get_current_admin_or_redirect
from app.services.house_service import HouseService
from app.services.settings_service import SettingsService
from app.schemas.house import HouseCreate, HouseUpdate
from app.web.help_texts import HELP_TEXTS

templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web/houses", tags=["web-houses"])

@router.get("/", response_class=HTMLResponse)
async def list_houses(
    request: Request,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Список домов"""
    houses = await HouseService.get_all_houses(db)
    project_settings = await SettingsService.get_project_settings(db)
    
    return templates.TemplateResponse(
        "houses/list.html",
        {
            "request": request,
            "project_name": project_settings.get("name"),
            "user": user,
            "houses": houses
        }
    )

@router.get("/new", response_class=HTMLResponse)
async def new_house_form(
    request: Request,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Форма создания дома"""
    project_settings = await SettingsService.get_project_settings(db)
    return templates.TemplateResponse(
        "houses/form.html",
        {
            "request": request,
            "project_name": project_settings.get("name"),
            "user": user,
            "house": None, # New mode
            "help_texts": HELP_TEXTS
        }
    )

@router.post("/", response_class=HTMLResponse)
async def create_house(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    capacity: int = Form(2),
    wifi_info: Optional[str] = Form(None),
    checkin_instruction: Optional[str] = Form(None),
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Создание дома (все поля в MVP)"""
    new_house = HouseCreate(
        name=name,
        description=description,
        capacity=capacity,
        wifi_info=wifi_info,
        checkin_instruction=checkin_instruction
        # Add other dynamic fields as needed in form
    )
    await HouseService.create_house(db, new_house)
    
    return RedirectResponse(
        url="/admin-web/houses", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/{house_id}", response_class=HTMLResponse)
async def edit_house_form(
    request: Request,
    house_id: int,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Форма редактирования"""
    house = await HouseService.get_house_by_id(db, house_id)
    if not house:
        return RedirectResponse(url="/admin-web/houses", status_code=303)

    project_settings = await SettingsService.get_project_settings(db)
    return templates.TemplateResponse(
        "houses/form.html",
        {
            "request": request,
            "project_name": project_settings.get("name"),
            "user": user,
            "house": house, # Edit mode
            "help_texts": HELP_TEXTS
        }
    )

@router.post("/{house_id}", response_class=HTMLResponse)
async def update_house(
    request: Request,
    house_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    capacity: int = Form(...),
    wifi_info: Optional[str] = Form(None),
    checkin_instruction: Optional[str] = Form(None),
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Обновление дома"""
    update_data = HouseUpdate(
        name=name,
        description=description,
        capacity=capacity,
        wifi_info=wifi_info,
        checkin_instruction=checkin_instruction
    )
    await HouseService.update_house(db, house_id, update_data)
    
    return RedirectResponse(
        url="/admin-web/houses", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/{house_id}/delete", response_class=HTMLResponse)
async def delete_house(
    request: Request,
    house_id: int,
    user: User = Depends(get_current_admin_or_redirect),
    db: AsyncSession = Depends(get_db)
):
    """Удаление дома"""
    await HouseService.delete_house(db, house_id)
    return RedirectResponse(
        url="/admin-web/houses", 
        status_code=status.HTTP_303_SEE_OTHER
    )
