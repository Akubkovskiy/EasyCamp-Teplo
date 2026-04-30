---
source_file: "app\telegram\auth\admin.py"
type: "code"
community: "cleaner_task_flow.py / get_all_users()"
location: "L125"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/cleaner_task_flow.py_/_get_all_users()
---

# resolve_user_db_id()

## Connections
- [[_do_transition()]] - `calls` [INFERRED]
- [[admin.py]] - `contains` [EXTRACTED]
- [[cleaner_claim_submit()]] - `calls` [INFERRED]
- [[cleaner_receive_photo()]] - `calls` [INFERRED]
- [[cleaner_toggle_check()]] - `calls` [INFERRED]
- [[Возвращает PK `users.id` по `telegram_id`. Используется для записи     в FK-кол]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/cleaner_task_flow.py_/_get_all_users()