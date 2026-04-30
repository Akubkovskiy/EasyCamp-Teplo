---
source_file: "app\services\avito_sync_service.py"
type: "code"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L151"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# process_avito_booking()

## Connections
- [[Booking_1]] - `calls` [INFERRED]
- [[avito_sync_service.py]] - `contains` [EXTRACTED]
- [[extract_avito_contact_field()]] - `calls` [EXTRACTED]
- [[format_phone()_1]] - `calls` [INFERRED]
- [[map_avito_status()]] - `calls` [EXTRACTED]
- [[should_replace_avito_guest_value()]] - `calls` [INFERRED]
- [[str]] - `calls` [INFERRED]
- [[sync_avito_bookings()]] - `calls` [EXTRACTED]
- [[test_adjacent_dates_are_not_overlap()]] - `calls` [INFERRED]
- [[test_existing_booking_update_still_works()]] - `calls` [INFERRED]
- [[test_new_booking_with_overlap_is_skipped()]] - `calls` [INFERRED]
- [[test_new_booking_without_overlap_is_created()]] - `calls` [INFERRED]
- [[Обработка одной брони из Avito]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/test_avito_overlap_guard.py_/_process_avito_booking()