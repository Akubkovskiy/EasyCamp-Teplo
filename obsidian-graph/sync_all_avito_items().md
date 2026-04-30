---
source_file: "app\services\avito_sync_service.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L300"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# sync_all_avito_items()

## Connections
- [[avito_sync_service.py]] - `contains` [EXTRACTED]
- [[fetch_from_avito()]] - `calls` [INFERRED]
- [[sync_avito_bookings()]] - `calls` [EXTRACTED]
- [[sync_avito_job()]] - `calls` [INFERRED]
- [[Синхронизация всех объявлений Avito      Args         item_house_mapping Сл]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/test_avito_overlap_guard.py_/_process_avito_booking()