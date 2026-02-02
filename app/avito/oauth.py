"""
OAuth авторизация для Avito API
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import requests
import logging

from app.core.config import settings

router = APIRouter(prefix="/avito", tags=["avito-oauth"])
logger = logging.getLogger(__name__)

# Временное хранилище для токена (в продакшене использовать БД)
_token_storage = {"access_token": None, "refresh_token": None, "expires_at": None}


@router.get("/auth")
async def start_auth():
    """Начать OAuth авторизацию"""

    # Попробуем без scope - базовая авторизация
    auth_url = (
        f"https://avito.ru/oauth?"
        f"client_id={settings.avito_client_id}&"
        f"response_type=code&"
        f"redirect_uri={settings.avito_redirect_uri}"
    )

    return HTMLResponse(f"""
    <html>
        <head><title>Avito OAuth</title></head>
        <body>
            <h1>Авторизация Avito API (без scope)</h1>
            <p>Redirect URI: <code>{settings.avito_redirect_uri}</code></p>
            <p>Пробуем базовую авторизацию без специальных прав</p>
            <p>Нажмите кнопку для авторизации:</p>
            <a href="{auth_url}" style="
                display: inline-block;
                padding: 10px 20px;
                background: #0066ff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            ">Авторизовать приложение</a>
            
            <hr>
            <p><small>После авторизации вы будете перенаправлены обратно</small></p>
        </body>
    </html>
    """)


@router.get("/callback")
async def oauth_callback(request: Request, code: str = None, error: str = None):
    """Обработка callback от Avito"""

    # Логируем все параметры
    logger.info("OAuth callback received")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info(f"Code: {code}")
    logger.info(f"Error: {error}")

    if error:
        logger.error(f"OAuth error from Avito: {error}")
        return HTMLResponse(f"""
        <html>
            <body>
                <h1>❌ Ошибка авторизации</h1>
                <p>Error: {error}</p>
                <p>Query params: {dict(request.query_params)}</p>
            </body>
        </html>
        """)

    if not code:
        logger.error("No authorization code received")
        return HTMLResponse(f"""
        <html>
            <body>
                <h1>❌ Код авторизации не получен</h1>
                <p>Query params: {dict(request.query_params)}</p>
                <p><a href="/avito/auth">Попробовать снова</a></p>
            </body>
        </html>
        """)

    # Обмен кода на токен
    try:
        response = requests.post(
            "https://api.avito.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.avito_client_id,
                "client_secret": settings.avito_client_secret,
                "redirect_uri": settings.avito_redirect_uri,
            },
        )

        response.raise_for_status()
        data = response.json()

        # Сохраняем токены
        _token_storage["access_token"] = data.get("access_token")
        _token_storage["refresh_token"] = data.get("refresh_token")

        logger.info("OAuth successful! Token obtained.")

        return HTMLResponse(f"""
        <html>
            <body>
                <h1>✅ Авторизация успешна!</h1>
                <p>Access token получен</p>
                <p>Теперь можете использовать /fetch_avito в боте</p>
                
                <hr>
                <h3>Сохраните эти данные в .env:</h3>
                <pre>
AVITO_ACCESS_TOKEN={data.get("access_token")}
AVITO_REFRESH_TOKEN={data.get("refresh_token")}
                </pre>
            </body>
        </html>
        """)

    except Exception as e:
        logger.error(f"OAuth error: {e}")
        return HTMLResponse(f"""
        <html>
            <body>
                <h1>❌ Ошибка получения токена</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """)


def get_stored_token():
    """Получить сохраненный токен"""
    return _token_storage.get("access_token")
