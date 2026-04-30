---
source_file: "tests\test_cleaner_hardening.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L38"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# _seed_house_cleaner()

## Connections
- [[House]] - `calls` [INFERRED]
- [[User]] - `calls` [INFERRED]
- [[test_booking_cancel_propagates_to_active_task()]] - `calls` [EXTRACTED]
- [[test_booking_cancel_propagates_to_cleaning_task_and_ledger()]] - `calls` [EXTRACTED]
- [[test_cleaner_hardening.py]] - `contains` [EXTRACTED]
- [[test_cleaning_fee_accrued_once_on_done()]] - `calls` [EXTRACTED]
- [[test_supply_alert_open_idempotent_and_resolve()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()