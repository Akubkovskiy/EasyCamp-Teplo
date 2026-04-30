---
source_file: "tests\test_cleaner_hardening.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L86"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# test_cleaning_fee_accrued_once_on_done()

## Connections
- [[CleaningRate]] - `calls` [INFERRED]
- [[_make_session()]] - `calls` [EXTRACTED]
- [[_seed_booking_task()]] - `calls` [EXTRACTED]
- [[_seed_house_cleaner()]] - `calls` [EXTRACTED]
- [[test_cleaner_hardening.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()