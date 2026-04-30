---
source_file: "app\telegram\handlers\cleaner_task_flow.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L255"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Filter: только фото с caption `#taskN`. Без этого фильтра handler     проглатыв

## Connections
- [[CleaningTask]] - `uses` [INFERRED]
- [[CleaningTaskCheck]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[CleaningTaskStatus]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[_is_task_photo()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking