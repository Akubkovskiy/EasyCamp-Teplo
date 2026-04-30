---
source_file: "app\services\global_settings.py"
type: "code"
community: "guest.py / safe_edit()"
location: "L125"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/guest.py_/_safe_edit()
---

# compute_advance_amount()

## Connections
- [[Pure рассчитать сумму задатка от total_price по проценту.     Округление вниз д]] - `rationale_for` [EXTRACTED]
- [[_admin_approve_payment()]] - `calls` [INFERRED]
- [[_send_pay_receipt_to_admins()]] - `calls` [INFERRED]
- [[global_settings.py]] - `contains` [EXTRACTED]
- [[guest_pay()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/guest.py_/_safe_edit()