---
type: community
cohesion: 0.07
members: 28
---

# on_startup() / AutoSyncMiddleware

**Cohesion:** 0.07 - loosely connected
**Members:** 28 nodes

## Members
- [[.__call__()]] - code - app\telegram\middlewares\panel_guard.py
- [[.__call__()_1]] - code - app\telegram\middlewares\sync_middleware.py
- [[AutoSyncMiddleware]] - code - app\telegram\middlewares\sync_middleware.py
- [[BaseMiddleware]] - code
- [[Checks Google Drive for the latest backup and restores it     ONLY if the local]] - rationale - app\services\backup_service.py
- [[Creates a backup of the SQLite database and uploads it to Google Drive.]] - rationale - app\services\backup_service.py
- [[Middleware для автоматической синхронизации при обращении к боту      Синхрони]] - rationale - app\telegram\middlewares\sync_middleware.py
- [[Middleware для автоматической синхронизации с Google Sheets]] - rationale - app\telegram\middlewares\sync_middleware.py
- [[PanelGuardMiddleware]] - code - app\telegram\middlewares\panel_guard.py
- [[Telegram bot middlewares]] - rationale - app\telegram\middlewares\__init__.py
- [[__init__.py_8]] - code - app\telegram\middlewares\__init__.py
- [[auth_redirect_handler()]] - code - app\main.py
- [[backup_database_to_drive()]] - code - app\services\backup_service.py
- [[backup_service.py]] - code - app\services\backup_service.py
- [[commands.py]] - code - app\telegram\commands.py
- [[is_cleaner()]] - code - app\telegram\auth\admin.py
- [[main.py]] - code - app\main.py
- [[on_shutdown()]] - code - app\main.py
- [[on_startup()]] - code - app\main.py
- [[panel_guard.py]] - code - app\telegram\middlewares\panel_guard.py
- [[restore_latest_backup()]] - code - app\services\backup_service.py
- [[setup_commands()]] - code - app\telegram\commands.py
- [[sync_middleware.py]] - code - app\telegram\middlewares\sync_middleware.py
- [[Глобальный guard для callback-панелей.      Блокирует на уровне middleware выз]] - rationale - app\telegram\middlewares\panel_guard.py
- [[Обработчик middleware          Запускает синхронизацию перед обработкой сообще]] - rationale - app\telegram\middlewares\sync_middleware.py
- [[Проверяет, является ли пользователь уборщицей]] - rationale - app\telegram\auth\admin.py
- [[Регистрация Bot Menu Commands (кнопка Menu слева от поля ввода).  Разные набор]] - rationale - app\telegram\commands.py
- [[Устанавливает команды бота для всех scope.]] - rationale - app\telegram\commands.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/on_startup()_/_AutoSyncMiddleware
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 2 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 1 edge to [[_COMMUNITY_booking_service.py  create_or_update_avito_booking()]]
- 1 edge to [[_COMMUNITY_is_admin()  guest_booking.py]]

## Top bridge nodes
- [[on_startup()]] - degree 6, connects to 2 communities
- [[is_cleaner()]] - degree 4, connects to 1 community
- [[Проверяет, является ли пользователь уборщицей]] - degree 3, connects to 1 community
- [[.__call__()]] - degree 3, connects to 1 community