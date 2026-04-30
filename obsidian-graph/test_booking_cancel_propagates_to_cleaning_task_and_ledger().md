---
source_file: "tests\test_cleaner_hardening.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L200"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# test_booking_cancel_propagates_to_cleaning_task_and_ledger()

## Connections
- [[CleaningRate]] - `calls` [INFERRED]
- [[_make_session()]] - `calls` [EXTRACTED]
- [[_seed_booking_task()]] - `calls` [EXTRACTED]
- [[_seed_house_cleaner()]] - `calls` [EXTRACTED]
- [[cancel_booking должен     - перевести task в CANCELLED     - погасить cleaning_]] - `rationale_for` [EXTRACTED]
- [[test_cleaner_hardening.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()