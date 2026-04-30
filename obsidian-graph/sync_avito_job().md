---
source_file: "app\jobs\avito_sync_job.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L14"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# sync_avito_job()

## Connections
- [[avito_sync_job.py]] - `contains` [EXTRACTED]
- [[notify_new_bookings()]] - `calls` [EXTRACTED]
- [[notify_updated_bookings()]] - `calls` [EXTRACTED]
- [[sync_all_avito_items()]] - `calls` [INFERRED]
- [[sync_and_open_table()]] - `calls` [INFERRED]
- [[verify_local_bookings_in_avito()]] - `calls` [EXTRACTED]
- [[Периодическая синхронизация броней из Avito]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/test_avito_overlap_guard.py_/_process_avito_booking()