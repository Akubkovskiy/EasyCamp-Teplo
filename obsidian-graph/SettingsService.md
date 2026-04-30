---
source_file: "app\services\settings_service.py"
type: "code"
community: "login() / get_password_hash()"
location: "L6"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# SettingsService

## Connections
- [[GlobalSetting]] - `uses` [INFERRED]
- [[settings_service.py]] - `contains` [EXTRACTED]
- [[Обработка входа.      Сначала пробуем env-fallback (`ADMIN_WEB_USERNAME`  `AD]] - `uses` [INFERRED]
- [[Страница входа в админ-панель]] - `uses` [INFERRED]
- [[Страница редактирования настроек]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/login()_/_get_password_hash()