---
source_file: "app\telegram\auth\admin.py"
type: "code"
community: "guest.py / safe_edit()"
location: "L71"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/guest.py_/_safe_edit()
---

# remove_user()

## Connections
- [[admin.py]] - `contains` [EXTRACTED]
- [[refresh_users_cache()]] - `calls` [EXTRACTED]
- [[remove_user_handler()]] - `calls` [INFERRED]
- [[Удаляет пользователя из БД и обновляет кеш]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/guest.py_/_safe_edit()