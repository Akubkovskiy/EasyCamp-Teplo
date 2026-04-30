---
source_file: "app\services\avito_sync_service.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L22"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# extract_avito_contact_field()

## Connections
- [[Read Avito guest contact fields from nested contact or legacy top-level payload]] - `rationale_for` [EXTRACTED]
- [[avito_sync_service.py]] - `contains` [EXTRACTED]
- [[process_avito_booking()]] - `calls` [EXTRACTED]
- [[test_sync_service_extracts_name_from_dict_contact()]] - `calls` [INFERRED]
- [[test_sync_service_falls_back_to_legacy_top_level_fields()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()