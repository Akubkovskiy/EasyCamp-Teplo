from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

# Инициализация шаблонизатора (путь относительно корня проекта, или абсолютный)
# Предполагаем запуск из корня проекта
templates = Jinja2Templates(directory="app/web/templates")

router = APIRouter(prefix="/admin-web", tags=["web-admin"])

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа в админ-панель"""
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request,
            "project_name": settings.project_name
        }
    )
