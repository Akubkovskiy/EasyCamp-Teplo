---
source_file: "tests\test_cleaner_hardening.py"
type: "code"
community: "booking_service.py / create_or_update_avito_booking()"
location: "L1"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/booking_service.py_/_create_or_update_avito_booking()
---

# test_cleaner_hardening.py

## Connections
- [[_make_session()]] - `contains` [EXTRACTED]
- [[_seed_booking_task()]] - `contains` [EXTRACTED]
- [[_seed_house_cleaner()]] - `contains` [EXTRACTED]
- [[test_booking_cancel_propagates_to_active_task()]] - `contains` [EXTRACTED]
- [[test_booking_cancel_propagates_to_cleaning_task_and_ledger()]] - `contains` [EXTRACTED]
- [[test_cleaning_fee_accrued_once_on_done()]] - `contains` [EXTRACTED]
- [[test_supply_alert_open_idempotent_and_resolve()]] - `contains` [EXTRACTED]
- [[Тесты Phase C10 (cleaner hardening) accrual, supply_alert, booking cancel propa]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/booking_service.py_/_create_or_update_avito_booking()