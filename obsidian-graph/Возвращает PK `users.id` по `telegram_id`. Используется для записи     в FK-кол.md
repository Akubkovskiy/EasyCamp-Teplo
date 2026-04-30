---
source_file: "app\telegram\auth\admin.py"
type: "rationale"
community: "cleaner_task_flow.py / get_all_users()"
location: "L126"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/cleaner_task_flow.py_/_get_all_users()
---

# Возвращает PK `users.id` по `telegram_id`. Используется для записи     в FK-кол

## Connections
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[resolve_user_db_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/cleaner_task_flow.py_/_get_all_users()