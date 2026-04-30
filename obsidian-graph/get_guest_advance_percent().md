---
source_file: "app\services\global_settings.py"
type: "code"
community: "guest.py / safe_edit()"
location: "L114"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/guest.py_/_safe_edit()
---

# get_guest_advance_percent()

## Connections
- [[% от total_price, который гость вносит как задаток при бронировании.     Остаток]] - `rationale_for` [EXTRACTED]
- [[_admin_approve_payment()]] - `calls` [INFERRED]
- [[_send_pay_receipt_to_admins()]] - `calls` [INFERRED]
- [[get_int()]] - `calls` [EXTRACTED]
- [[global_settings.py]] - `contains` [EXTRACTED]
- [[guest_pay()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/guest.py_/_safe_edit()