import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Загрузка переменных из .env
load_dotenv()


class Settings(BaseModel):
    telegram_bot_token: str
    telegram_chat_id: int
    database_url: str = "sqlite+aiosqlite:///./easycamp.db"

    # Google Sheets
    google_sheets_spreadsheet_id: str = ""
    google_sheets_credentials_file: str = "google-credentials.json"

    # Avito API
    avito_client_id: str = ""
    avito_client_secret: str = ""
    avito_user_id: int = 75878034
    avito_item_ids: str = ""
    avito_redirect_uri: str = "http://localhost:8000/avito/callback"

    # Scheduler settings
    enable_auto_sync: bool = True
    avito_sync_interval_minutes: int = 5
    sheets_sync_interval_minutes: int = 5

    # Sync behavior settings
    sync_on_bot_start: bool = True
    sync_on_user_interaction: bool = True
    sync_cache_ttl_seconds: int = 30

    # Avito calendar settings
    booking_window_days: int = 180

    # Cleaner settings
    cleaning_notification_time: str = "20:00"
    cleaning_confirm_window_min: int = 30
    cleaning_sla_check_interval_minutes: int = 5

    # Webhook security settings
    # Mode: "off" = no verification, "warn" = log warning but allow, "enforce" = reject invalid
    avito_webhook_mode: str = "warn"  # Default: warn (safe rollout)
    avito_webhook_secret: str = ""  # If empty, behaves as "off" mode

    # Rate limiting settings
    rate_limit_enabled: bool = True  # Killswitch for quick disable
    rate_limit_webhook: str = "30/minute"  # Default: 30 requests per minute per IP

    # Logging settings
    log_format: str = "console"  # Options: "console", "json"
    log_slow_request_threshold_ms: int = 500  # Log timing only if duration > threshold

    # ----------------------------------------------------
    # SaaS / Branding Settings (De-branding)
    # ----------------------------------------------------
    project_name: str = "EasyCamp-Teplo"
    project_location: str = "Архыз"
    project_address: str = "с. Архыз, ул. Банковская, 26д"
    project_coords: str = "43.560731, 41.284236"  # Default fallback

    # Contacts
    contact_phone: str = "+7 928 000-00-00"
    admin_web_url: str = "https://teplo-v-arkhyze.ru/admin-web"
    contact_admin_username: str = "@sergey_teplo"
    contact_email: str = "info@easycamp.ru"
    contact_work_hours: str = "Круглосуточно"
    contact_website: str = "https://teplo-v-arkhyze.ru"
    yandex_reviews_url: str = ""  # Ссылка на отзывы в Яндекс.Картах (задать в .env)

    # Payment Info
    payment_receiver: str = "Сергей Иванович П."
    payment_methods: str = "Сбер/Тинькофф"

    # Pricing settings
    enable_auto_discounts: bool = True  # Авто-скидки на горящие даты
    enable_avito_price_sync: bool = True  # Синхронизация цен → Авито
    auto_discount_tomorrow_percent: int = 20  # Скидка если свободно завтра
    auto_discount_day_after_percent: int = 15  # Скидка если свободно послезавтра

    # Guest feature flags (SaaS toggles)
    guest_feature_faq: bool = True
    guest_feature_partners: bool = True
    guest_feature_showcase_houses: bool = True

    # Security
    secret_key: str = "dev_secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    setup_secret: str = "easycamp_secret"

    # Яндекс Путешествия White Label Partner API
    # Документация: https://yandex.ru/dev/travel-partners-api/doc/ru/
    # Токен действует 1 год. Генерируется через OAuth:
    #   https://oauth.yandex.ru/authorize?response_type=token&client_id=b0ca9cd48f66420c9995c0776f2243a8
    yandex_travel_oauth_token: str = ""
    # Маппинг номеров → домиков. Формат: "hotel_id/room_id:house_id,..."
    # Пример: "YA1234/ROOM1:1,YA1234/ROOM2:2"
    # hotel_id и room_id узнаются в Яндекс Путешествиях после активации доступа.
    yandex_travel_room_ids: str = ""
    yandex_travel_sync_interval_minutes: int = 15
    enable_yandex_travel_sync: bool = True
    enable_yandex_travel_price_sync: bool = True

    # Site lead intake (Phase S10) — публичный endpoint /api/leads
    # принимает заявки с teplo-v-arkhyze.ru. Token обязателен, иначе 401.
    site_lead_token: str = ""

    # Env-based admin web login (override / fallback to DB users.username).
    # Если оба заданы — сравнение по этим креденшелам идёт ДО запроса в БД.
    # Это удобно для первичного входа после деплоя или когда DB-пароль
    # потерян. Пустые строки = отключено.
    admin_web_username: str = ""
    admin_web_password: str = ""


# Resolve database URL with preference for Docker volume path
env_db_url = os.environ.get("DATABASE_URL")
if not env_db_url or "./easycamp.db" in env_db_url:
    if os.path.exists("/app/data/easycamp.db"):
        final_db_url = "sqlite+aiosqlite:////app/data/easycamp.db"
    else:
        final_db_url = "sqlite+aiosqlite:///./easycamp.db"
else:
    final_db_url = env_db_url

settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
    database_url=final_db_url,
    google_sheets_spreadsheet_id=os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
    google_sheets_credentials_file=os.environ.get(
        "GOOGLE_SHEETS_CREDENTIALS_FILE", "google-credentials.json"
    ),
    avito_client_id=os.environ.get("AVITO_CLIENT_ID", ""),
    avito_client_secret=os.environ.get("AVITO_CLIENT_SECRET", ""),
    avito_item_ids=os.environ.get("AVITO_ITEM_IDS", ""),
    avito_redirect_uri=os.environ.get(
        "AVITO_REDIRECT_URI", "http://localhost:8000/avito/callback"
    ),
    enable_auto_sync=os.environ.get("ENABLE_AUTO_SYNC", "true").lower() == "true",
    avito_sync_interval_minutes=int(os.environ.get("AVITO_SYNC_INTERVAL_MINUTES", "5")),
    sheets_sync_interval_minutes=int(
        os.environ.get("SHEETS_SYNC_INTERVAL_MINUTES", "5")
    ),
    sync_on_bot_start=os.environ.get("SYNC_ON_BOT_START", "true").lower() == "true",
    sync_on_user_interaction=os.environ.get("SYNC_ON_USER_INTERACTION", "true").lower()
    == "true",
    sync_cache_ttl_seconds=int(os.environ.get("SYNC_CACHE_TTL_SECONDS", "30")),
    booking_window_days=int(os.environ.get("BOOKING_WINDOW_DAYS", "180")),
    cleaning_notification_time=os.environ.get("CLEANING_NOTIFICATION_TIME", "20:00"),
    cleaning_confirm_window_min=int(os.environ.get("CLEANING_CONFIRM_WINDOW_MIN", "30")),
    cleaning_sla_check_interval_minutes=int(os.environ.get("CLEANING_SLA_CHECK_INTERVAL_MINUTES", "5")),
    avito_webhook_mode=os.environ.get("AVITO_WEBHOOK_MODE", "warn"),
    avito_webhook_secret=os.environ.get("AVITO_WEBHOOK_SECRET", ""),
    rate_limit_enabled=os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true",
    rate_limit_webhook=os.environ.get("RATE_LIMIT_WEBHOOK", "30/minute"),
    log_format=os.environ.get("LOG_FORMAT", "console"),
    log_slow_request_threshold_ms=int(
        os.environ.get("LOG_SLOW_REQUEST_THRESHOLD_MS", "500")
    ),
    # SaaS Settings
    project_name=os.environ.get("PROJECT_NAME", "EasyCamp-Teplo"),
    project_location=os.environ.get("PROJECT_LOCATION", "Архыз"),
    project_address=os.environ.get("PROJECT_ADDRESS", "с. Архыз, ул. Банковская, 26д"),
    project_coords=os.environ.get("PROJECT_COORDS", "43.560731, 41.284236"),
    contact_phone=os.environ.get("CONTACT_PHONE", "+7 928 000-00-00"),
    admin_web_url=os.environ.get("ADMIN_WEB_URL", "https://teplo-v-arkhyze.ru/admin-web"),
    contact_admin_username=os.environ.get("CONTACT_ADMIN_USERNAME", "@sergey_teplo"),
    contact_email=os.environ.get("CONTACT_EMAIL", "info@easycamp.ru"),
    contact_work_hours=os.environ.get("CONTACT_WORK_HOURS", "Круглосуточно"),
    contact_website=os.environ.get("CONTACT_WEBSITE", "https://teplo-v-arkhyze.ru"),
    yandex_reviews_url=os.environ.get("YANDEX_REVIEWS_URL", ""),
    payment_receiver=os.environ.get("PAYMENT_RECEIVER", "Сергей Иванович П."),
    payment_methods=os.environ.get("PAYMENT_METHODS", "Сбер/Тинькофф"),
    enable_auto_discounts=os.environ.get("ENABLE_AUTO_DISCOUNTS", "true").lower() == "true",
    enable_avito_price_sync=os.environ.get("ENABLE_AVITO_PRICE_SYNC", "true").lower() == "true",
    auto_discount_tomorrow_percent=int(os.environ.get("AUTO_DISCOUNT_TOMORROW_PERCENT", "20")),
    auto_discount_day_after_percent=int(os.environ.get("AUTO_DISCOUNT_DAY_AFTER_PERCENT", "15")),
    guest_feature_faq=os.environ.get("GUEST_FEATURE_FAQ", "true").lower() == "true",
    guest_feature_partners=os.environ.get("GUEST_FEATURE_PARTNERS", "true").lower() == "true",
    guest_feature_showcase_houses=os.environ.get("GUEST_FEATURE_SHOWCASE_HOUSES", "true").lower() == "true",
    secret_key=os.environ.get("SECRET_KEY", "dev_secret_key_change_me"),
    algorithm="HS256",
    access_token_expire_minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))),
    setup_secret=os.environ.get("SETUP_SECRET", "easycamp_secret"),
    yandex_travel_oauth_token=os.environ.get("YANDEX_TRAVEL_OAUTH_TOKEN", ""),
    yandex_travel_room_ids=os.environ.get("YANDEX_TRAVEL_ROOM_IDS", ""),
    yandex_travel_sync_interval_minutes=int(os.environ.get("YANDEX_TRAVEL_SYNC_INTERVAL_MINUTES", "15")),
    enable_yandex_travel_sync=os.environ.get("ENABLE_YANDEX_TRAVEL_SYNC", "true").lower() == "true",
    enable_yandex_travel_price_sync=os.environ.get("ENABLE_YANDEX_TRAVEL_PRICE_SYNC", "true").lower() == "true",
    site_lead_token=os.environ.get("SITE_LEAD_TOKEN", ""),
    admin_web_username=os.environ.get("ADMIN_WEB_USERNAME", ""),
    admin_web_password=os.environ.get("ADMIN_WEB_PASSWORD", ""),
)

# Startup security warnings — log once at import time
import logging as _logging
_sec_log = _logging.getLogger("easycamp.security")

if settings.secret_key in ("dev_secret", "dev_secret_key_change_me"):
    _sec_log.warning("SECRET_KEY is using an insecure default — set SECRET_KEY in .env")

if settings.setup_secret == "easycamp_secret":
    _sec_log.warning("SETUP_SECRET is using an insecure default — set SETUP_SECRET in .env")
