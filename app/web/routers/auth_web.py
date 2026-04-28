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
    """Обработка входа.

    Сначала пробуем env-fallback (`ADMIN_WEB_USERNAME` / `ADMIN_WEB_PASSWORD`).
    Если оба заданы и совпали — пускаем без обращения к БД (создаём
    или находим запись `User(role=ADMIN)` чтобы выдать корректный токен).
    Иначе — обычная проверка по `users.username` + bcrypt.
    """
    env_user = (settings.admin_web_username or "").strip()
    env_pass = (settings.admin_web_password or "").strip()
    user = None

    if env_user and env_pass and username == env_user and password == env_pass:
        # Try to attach env login to an existing User row, чтобы access-token
        # имел стабильный sub. Если такой записи нет — создаём.
        stmt = select(User).where(User.username == env_user)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            # Минимальная запись; password здесь не используется (env
            # перебивает), но поле ненулёвое для совместимости со схемой.
            from app.core.security import get_password_hash
            from app.models import UserRole

            user = User(
                username=env_user,
                hashed_password=get_password_hash(env_pass),
                role=UserRole.ADMIN,
                name="Env Admin",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

    # 1. Если env-вход не сработал — обычная проверка по БД
    if user is None:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

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
