---
source_file: "app\telegram\handlers\avito_fetch.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L16"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# fetch_from_avito()

## Connections
- [[avito_fetch.py]] - `contains` [EXTRACTED]
- [[notify_new_bookings()]] - `calls` [INFERRED]
- [[notify_updated_bookings()]] - `calls` [INFERRED]
- [[str]] - `calls` [INFERRED]
- [[sync_all_avito_items()]] - `calls` [INFERRED]
- [[Получить брони из Avito API]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/test_avito_overlap_guard.py_/_process_avito_booking()