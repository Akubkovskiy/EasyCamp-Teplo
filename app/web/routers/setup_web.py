from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.services.setup_service import SetupStateService
from app.web.help_texts import HELP_TEXTS
from app.web.help_texts import HELP_TEXTS

templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web/setup", tags=["web-setup"])

SETUP_SECRET = settings.setup_secret or "easycamp_secret"  # Fallback only for DEV

@router.get("/", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Страница первого запуска (ввод секрета)"""
    return templates.TemplateResponse(
        "setup_intro.html",
        {
            "request": request,
            "project_name": "EasyCamp Setup",
            "error": request.query_params.get("error")
        }
    )

@router.post("/", response_class=HTMLResponse)
async def check_secret(
    request: Request,
    secret: str = Form(...)
):
    """Проверка секрета и старт сессии"""
    if secret != SETUP_SECRET:
        return templates.TemplateResponse(
            "setup_intro.html",
            {
                "request": request,
                "project_name": "EasyCamp Setup",
                "error": "Неверный секретный ключ"
            },
            status_code=403
        )

    # Set setup_token cookie (simple hash of secret for now)
    response = RedirectResponse(url="/admin-web/setup/step1", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="setup_token", value="valid", httponly=True) 
    return response

@router.get("/step1", response_class=HTMLResponse)
async def step1_page(request: Request):
    """Шаг 1: Идентичность проекта"""
    # Verify cookie (simple check)
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    return templates.TemplateResponse(
        "setup_step1.html",
        {
            "request": request,
            "project_name": "EasyCamp Setup",
            "settings": settings # Pre-fill with defaults
        }
    )

@router.post("/step1", response_class=HTMLResponse)
async def step1_save(
    request: Request,
    project_name: str = Form(...),
    project_location: str = Form(...),
    contact_phone: str = Form(...),
    project_address: str = Form(""),
    contact_admin: str = Form(""),
):
    """Сохранение шага 1 -> Переход к Шагу 2"""
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    async with AsyncSessionLocal() as db:
        async def save_setting(key, val):
            from app.models import GlobalSetting
            from sqlalchemy import select
            
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
        await db.commit()

    return RedirectResponse(url="/admin-web/setup/step2", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/step2", response_class=HTMLResponse)
async def step2_page(request: Request):
    """Шаг 2: AI Настройки"""
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    return templates.TemplateResponse(
        "setup_step2.html",
        {
            "request": request,
            "project_name": "EasyCamp Setup",
            "settings": settings 
        }
    )

@router.post("/step2", response_class=HTMLResponse)
async def step2_save(
    request: Request,
    ai_enabled: str = Form(...),
    spreadsheet_id: str = Form("")
):
    """Сохранение шага 2 -> Завершение"""
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    async with AsyncSessionLocal() as db:
        async def save_setting(key, val):
            from app.models import GlobalSetting
            from sqlalchemy import select
            
            stmt = select(GlobalSetting).where(GlobalSetting.key == key)
            res = await db.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                db.add(GlobalSetting(key=key, value=val))
            else:
                obj.value = val

        await save_setting("ai_enabled", ai_enabled)
        await save_setting("google_sheets_spreadsheet_id", spreadsheet_id)
        await db.commit()

    return RedirectResponse(url="/admin-web/setup/step3", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/step3", response_class=HTMLResponse)
async def step3_page(request: Request):
    """Шаг 3: Создание Администратора"""
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    return templates.TemplateResponse(
        "setup_step3.html",
        {
            "request": request,
            "project_name": "EasyCamp Setup",
        }
    )

@router.post("/step3", response_class=HTMLResponse)
async def step3_save(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form("Owner"),
):
    """Создание админа и Завершение"""
    if request.cookies.get("setup_token") != "valid":
        return RedirectResponse(url="/admin-web/setup", status_code=303)

    from app.services.setup_service import SetupStateService
    from app.models import User, UserRole
    from app.core.security import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # 1. Create Owner User
        stmt = select(User).where(User.username == username)
        res = await db.execute(stmt)
        existing_user = res.scalar_one_or_none()
        
        if not existing_user:
            new_user = User(
                username=username,
                hashed_password=get_password_hash(password),
                role=UserRole.OWNER,
                name=name,
                phone="" # Optional
            )
            db.add(new_user)
        else:
            # Update existing if specifically this one (idempotency for setup loops)
            existing_user.hashed_password = get_password_hash(password)
            existing_user.role = UserRole.OWNER
            existing_user.name = name
        
        # 2. Mark Setup Done
        await SetupStateService.set_initial_setup_done(db, True)
        
        await db.commit()

    resp = RedirectResponse(url="/admin-web/login?msg=setup_complete", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("setup_token")
    return resp
