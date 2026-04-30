---
type: community
cohesion: 0.03
members: 81
---

# str / settings.py

**Cohesion:** 0.03 - loosely connected
**Members:** 81 nodes

## Members
- [[.dispatch()]] - code - app\middleware\request_logger.py
- [[.dispatch()_1]] - code - app\web\middleware\setup_middleware.py
- [[BaseHTTPMiddleware]] - code
- [[Middleware to log slow requests timing and metadata.     Logs method, path, st]] - rationale - app\middleware\request_logger.py
- [[OAuth авторизация для Avito API]] - rationale - app\avito\oauth.py
- [[RequestLoggerMiddleware]] - code - app\middleware\request_logger.py
- [[SetupMiddleware]] - code - app\web\middleware\setup_middleware.py
- [[apply_booking_window()]] - code - app\telegram\handlers\settings.py
- [[auto_discount_job()]] - code - app\jobs\pricing_job.py
- [[avito_price_service.py]] - code - app\services\avito_price_service.py
- [[avito_price_sync_job()]] - code - app\jobs\pricing_job.py
- [[back_to_settings()]] - code - app\telegram\handlers\settings.py
- [[booking_window_settings()]] - code - app\telegram\handlers\settings.py
- [[check_db_and_sync.py]] - code - scripts\check_db_and_sync.py
- [[cleaning_time_settings()]] - code - app\telegram\handlers\settings.py
- [[edit_avito_interval()]] - code - app\telegram\handlers\settings.py
- [[edit_booking_window()]] - code - app\telegram\handlers\settings.py
- [[edit_sheets_interval()]] - code - app\telegram\handlers\settings.py
- [[get_sheet_link()]] - code - app\telegram\handlers\sync.py
- [[get_stored_token()]] - code - app\avito\oauth.py
- [[main()_1]] - code - scripts\check_db_and_sync.py
- [[oauth.py]] - code - app\avito\oauth.py
- [[oauth_callback()]] - code - app\avito\oauth.py
- [[parse_avito_item_ids()]] - code - app\services\avito_price_service.py
- [[pricing_cycle_job()]] - code - app\jobs\pricing_job.py
- [[pricing_job.py]] - code - app\jobs\pricing_job.py
- [[pricing_settings()]] - code - app\telegram\handlers\settings.py
- [[request_logger.py]] - code - app\middleware\request_logger.py
- [[run_pricing_cycle_now()]] - code - app\telegram\handlers\settings.py
- [[set_avito_interval()]] - code - app\telegram\handlers\settings.py
- [[set_booking_window()]] - code - app\telegram\handlers\settings.py
- [[set_cleaning_time()]] - code - app\telegram\handlers\settings.py
- [[set_sheets_interval()]] - code - app\telegram\handlers\settings.py
- [[settings.py]] - code - app\telegram\handlers\settings.py
- [[settings_page()]] - code - app\web\routers\settings_web.py
- [[settings_save()]] - code - app\web\routers\settings_web.py
- [[settings_web.py]] - code - app\web\routers\settings_web.py
- [[setup_middleware.py]] - code - app\web\middleware\setup_middleware.py
- [[show_settings()]] - code - app\telegram\handlers\settings.py
- [[start_auth()]] - code - app\avito\oauth.py
- [[str]] - code
- [[sync.py]] - code - app\telegram\handlers\sync.py
- [[sync_house_avito_prices()]] - code - app\telegram\handlers\houses.py
- [[sync_prices_to_avito()]] - code - app\services\avito_price_service.py
- [[sync_settings()]] - code - app\telegram\handlers\settings.py
- [[sync_to_sheets()]] - code - app\telegram\handlers\sync.py
- [[toggle_auto_discounts()]] - code - app\telegram\handlers\settings.py
- [[toggle_avito_price_sync()]] - code - app\telegram\handlers\settings.py
- [[update_env_variable()]] - code - app\telegram\handlers\settings.py
- [[Вернуться к настройкам]] - rationale - app\telegram\handlers\settings.py
- [[Изменить интервал Avito]] - rationale - app\telegram\handlers\settings.py
- [[Изменить интервал Sheets]] - rationale - app\telegram\handlers\settings.py
- [[Изменить период бронирования]] - rationale - app\telegram\handlers\settings.py
- [[Настройки времени уведомлений об уборке]] - rationale - app\telegram\handlers\settings.py
- [[Настройки периода бронирования]] - rationale - app\telegram\handlers\settings.py
- [[Настройки синхронизации]] - rationale - app\telegram\handlers\settings.py
- [[Настройки ценообразования]] - rationale - app\telegram\handlers\settings.py
- [[Начать OAuth авторизацию]] - rationale - app\avito\oauth.py
- [[Обновить переменную в .env файле]] - rationale - app\telegram\handlers\settings.py
- [[Обработка callback от Avito]] - rationale - app\avito\oauth.py
- [[Обработчики для синхронизации с Google Sheets]] - rationale - app\telegram\handlers\sync.py
- [[Обработчики настроек бота]] - rationale - app\telegram\handlers\settings.py
- [[Парсит AVITO_ITEM_IDS из настроек.     Формат avito_item_idhouse_id,avito_it]] - rationale - app\services\avito_price_service.py
- [[Периодические задачи ценообразования 1. Авто-скидки на свободные даты (горящие]] - rationale - app\jobs\pricing_job.py
- [[Полный цикл сначала проверяем скидки, потом синхронизируем цены на Авито.]] - rationale - app\jobs\pricing_job.py
- [[Получить сохраненный токен]] - rationale - app\avito\oauth.py
- [[Получить ссылку на Google таблицу]] - rationale - app\telegram\handlers\sync.py
- [[Применить период бронирования ко всем домам]] - rationale - app\telegram\handlers\settings.py
- [[Проверка БД и синхронизация с Google Sheets]] - rationale - scripts\check_db_and_sync.py
- [[Проверяет загруженность на ближайшие дни.     Если домик свободен завтрапослез]] - rationale - app\jobs\pricing_job.py
- [[Ручной запуск цикла ценообразования]] - rationale - app\telegram\handlers\settings.py
- [[Сервис синхронизации цен с Avito. Берёт цены из базы (base_price + сезонные + с]] - rationale - app\services\avito_price_service.py
- [[Синхронизировать данные с Google Sheets]] - rationale - app\telegram\handlers\sync.py
- [[Синхронизирует текущие цены (base + сезонные + скидки) на Авито.     Запускаетс]] - rationale - app\jobs\pricing_job.py
- [[Синхронизирует цены из базы на Авито.      Args         db Сессия БД]] - rationale - app\services\avito_price_service.py
- [[Скрипт для проверки данных в БД и синхронизации с Google Sheets]] - rationale - scripts\check_db_and_sync.py
- [[Страница редактирования настроек]] - rationale - app\web\routers\settings_web.py
- [[Установить время уведомлений]] - rationale - app\telegram\handlers\settings.py
- [[Установить интервал Avito]] - rationale - app\telegram\handlers\settings.py
- [[Установить интервал Sheets]] - rationale - app\telegram\handlers\settings.py
- [[Установить период бронирования]] - rationale - app\telegram\handlers\settings.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/str_/_settings.py
SORT file.name ASC
```

## Connections to other communities
- 26 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 5 edges to [[_COMMUNITY_test_avito_overlap_guard.py  process_avito_booking()]]
- 3 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 2 edges to [[_COMMUNITY_booking_service.py  create_or_update_avito_booking()]]
- 2 edges to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 2 edges to [[_COMMUNITY_login()  get_password_hash()]]
- 2 edges to [[_COMMUNITY_GlobalSetting  global_settings.py]]
- 1 edge to [[_COMMUNITY_avito_webhook()  Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s]]
- 1 edge to [[_COMMUNITY_cleaner.py  show_cleaner_menu()]]
- 1 edge to [[_COMMUNITY_create.py  build_month_keyboard()]]
- 1 edge to [[_COMMUNITY_houses.py  HouseUpdate]]
- 1 edge to [[_COMMUNITY_NotificationRule  NotificationService]]

## Top bridge nodes
- [[str]] - degree 35, connects to 9 communities
- [[Страница редактирования настроек]] - degree 4, connects to 3 communities
- [[settings.py]] - degree 21, connects to 2 communities
- [[SetupMiddleware]] - degree 4, connects to 1 community
- [[Скрипт для проверки данных в БД и синхронизации с Google Sheets]] - degree 3, connects to 1 community