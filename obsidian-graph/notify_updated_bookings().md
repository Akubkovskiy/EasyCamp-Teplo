---
source_file: "app\jobs\avito_sync_job.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L184"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# notify_updated_bookings()

## Connections
- [[avito_sync_job.py]] - `contains` [EXTRACTED]
- [[fetch_from_avito()]] - `calls` [INFERRED]
- [[sync_avito_job()]] - `calls` [EXTRACTED]
- [[Отправить уведомление об обновлении броней]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/test_avito_overlap_guard.py_/_process_avito_booking()