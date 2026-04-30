---
source_file: "tests\test_cleaner_hardening.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L271"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# test_booking_cancel_propagates_to_active_task()

## Connections
- [[_make_session()]] - `calls` [EXTRACTED]
- [[_seed_booking_task()]] - `calls` [EXTRACTED]
- [[_seed_house_cleaner()]] - `calls` [EXTRACTED]
- [[test_cleaner_hardening.py]] - `contains` [EXTRACTED]
- [[Если задача ещё в IN_PROGRESS  PENDING  ACCEPTED — cancel должен     перевести]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()