---
source_file: "app\services\cleaning_task_service.py"
type: "code"
community: "cleaning_task_service.py / transition_status()"
location: "L145"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/cleaning_task_service.py_/_transition_status()
---

# ensure_default_checklist()

## Connections
- [[CleaningTaskCheck]] - `calls` [INFERRED]
- [[cleaning_task_service.py]] - `contains` [EXTRACTED]
- [[create_task_for_booking()]] - `calls` [EXTRACTED]
- [[transition_status()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/cleaning_task_service.py_/_transition_status()