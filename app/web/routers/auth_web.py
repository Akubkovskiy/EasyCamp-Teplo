from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.database import get_db
from app.models import User
from app.core.security import verify_password, create_access_token

# Инициализация шаблонизатора (путь относительно корня проекта, или абсолютный)
# Предполагаем запуск из корня проекта
templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web", tags=["web-admin"])

from app.services.settings_service import SettingsService

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Страница входа в админ-панель"""
    project_settings = await SettingsService.get_project_settings(db)
    
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request,
            "project_name": project_settings.get("name") or settings.project_name,
            "error": request.query_params.get("error")
        }
    )

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Обработка входа"""
    # 1. Find user
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 2. Verify password
    if not user or not verify_password(password, user.hashed_password):
        project_settings = await SettingsService.get_project_settings(db)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "project_name": project_settings.get("name") or settings.project_name,
                "error": "Неверное имя пользователя или пароль"
            },
            status_code=401
        )

    # 3. Create Token
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    # 4. Set Cookie and Redirect
    response = RedirectResponse(url="/admin-web", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        expires=settings.access_token_expire_minutes * 60,
    )
    return response

@router.get("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/admin-web/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_token")
    return response
