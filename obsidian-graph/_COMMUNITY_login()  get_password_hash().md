---
type: community
cohesion: 0.06
members: 38
---

# login() / get_password_hash()

**Cohesion:** 0.06 - loosely connected
**Members:** 38 nodes

## Members
- [[AuthRedirectException]] - code - app\web\deps.py
- [[Custom exception for authentication redirects in web routes]] - rationale - app\web\deps.py
- [[Decodes a JWT token. Returns dict or raises error.]] - rationale - app\core\security.py
- [[Dependency to get current admin user from cookie session.     Redirects to adm]] - rationale - app\web\deps.py
- [[Exception]] - code
- [[Generates a hash from a plain password.]] - rationale - app\core\security.py
- [[Same as above but redirects to login page on failure.     Used for page routes.]] - rationale - app\web\deps.py
- [[SettingsService]] - code - app\services\settings_service.py
- [[Verifies a plain password against a hash.]] - rationale - app\core\security.py
- [[auth_web.py]] - code - app\web\routers\auth_web.py
- [[create_access_token()]] - code - app\core\security.py
- [[create_admin()]] - code - scripts\create_admin.py
- [[create_admin.py]] - code - scripts\create_admin.py
- [[decode_access_token()]] - code - app\core\security.py
- [[deps.py]] - code - app\web\deps.py
- [[ensure_admin()]] - code - scripts\verify_settings.py
- [[get_all_settings()]] - code - app\services\settings_service.py
- [[get_current_admin()]] - code - app\web\deps.py
- [[get_current_admin_or_redirect()]] - code - app\web\deps.py
- [[get_password_hash()]] - code - app\core\security.py
- [[get_project_settings()]] - code - app\services\settings_service.py
- [[login()]] - code - app\web\routers\auth_web.py
- [[login_page()]] - code - app\web\routers\auth_web.py
- [[logout()]] - code - app\web\routers\auth_web.py
- [[run_server()_1]] - code - scripts\verify_house_crud.py
- [[run_server()_2]] - code - scripts\verify_settings.py
- [[security.py]] - code - app\core\security.py
- [[settings_service.py]] - code - app\services\settings_service.py
- [[setup_test_env()]] - code - scripts\verify_house_crud.py
- [[smoke_test()]] - code - scripts\smoke_test.py
- [[smoke_test.py]] - code - scripts\smoke_test.py
- [[test_settings_flow()]] - code - scripts\verify_settings.py
- [[verify_crud()]] - code - scripts\verify_house_crud.py
- [[verify_house_crud.py]] - code - scripts\verify_house_crud.py
- [[verify_password()]] - code - app\core\security.py
- [[verify_settings.py]] - code - scripts\verify_settings.py
- [[Обработка входа.      Сначала пробуем env-fallback (`ADMIN_WEB_USERNAME`  `AD]] - rationale - app\web\routers\auth_web.py
- [[Страница входа в админ-панель]] - rationale - app\web\routers\auth_web.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/login()_/_get_password_hash()
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 2 edges to [[_COMMUNITY_str  settings.py]]
- 2 edges to [[_COMMUNITY_GlobalSetting  global_settings.py]]

## Top bridge nodes
- [[login()]] - degree 7, connects to 2 communities
- [[SettingsService]] - degree 5, connects to 2 communities
- [[get_password_hash()]] - degree 7, connects to 1 community
- [[AuthRedirectException]] - degree 6, connects to 1 community
- [[Страница входа в админ-панель]] - degree 4, connects to 1 community