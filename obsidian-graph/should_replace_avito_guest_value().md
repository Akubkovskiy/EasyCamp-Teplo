---
source_file: "app\services\booking_service.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L60"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# should_replace_avito_guest_value()

## Connections
- [[Replace only empty or placeholder values with a better Avito contact value.]] - `rationale_for` [EXTRACTED]
- [[booking_service.py]] - `contains` [EXTRACTED]
- [[create_or_update_avito_booking()]] - `calls` [EXTRACTED]
- [[process_avito_booking()]] - `calls` [INFERRED]
- [[test_do_not_override_existing_real_guest_name()]] - `calls` [INFERRED]
- [[test_replace_empty_phone_with_incoming_value()]] - `calls` [INFERRED]
- [[test_replace_placeholder_guest_name_with_real_value()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/booking_service.py_/_create_or_update_avito_booking()