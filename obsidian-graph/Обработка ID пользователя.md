---
source_file: "app\telegram\handlers\settings_users.py"
type: "rationale"
community: "cleaner_task_flow.py / get_all_users()"
location: "L131"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/cleaner_task_flow.py_/_get_all_users()
---

# Обработка ID пользователя

## Connections
- [[UserRole]] - `uses` [INFERRED]
- [[process_user_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/cleaner_task_flow.py_/_get_all_users()