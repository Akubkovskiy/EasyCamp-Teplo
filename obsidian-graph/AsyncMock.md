---
source_file: "scripts\test_sync_logic.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L14"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# AsyncMock

## Connections
- [[.__await__()]] - `method` [EXTRACTED]
- [[.__call__()_2]] - `method` [EXTRACTED]
- [[MagicMock]] - `inherits` [EXTRACTED]
- [[test_adjacent_dates_are_not_overlap()]] - `calls` [INFERRED]
- [[test_existing_booking_update_still_works()]] - `calls` [INFERRED]
- [[test_new_booking_with_overlap_is_skipped()]] - `calls` [INFERRED]
- [[test_new_booking_without_overlap_is_created()]] - `calls` [INFERRED]
- [[test_sync_logic.py]] - `contains` [EXTRACTED]
- [[test_webhook_new_booking_with_overlap_blocked()]] - `calls` [INFERRED]
- [[test_webhook_new_booking_without_overlap_created()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/test_avito_overlap_guard.py_/_process_avito_booking()