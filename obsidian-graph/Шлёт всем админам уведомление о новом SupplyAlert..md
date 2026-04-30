---
source_file: "app\telegram\handlers\cleaner_task_flow.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L214"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Шлёт всем админам уведомление о новом SupplyAlert.

## Connections
- [[CleaningTask]] - `uses` [INFERRED]
- [[CleaningTaskCheck]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[CleaningTaskStatus]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[_notify_admins_supply_alert()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking