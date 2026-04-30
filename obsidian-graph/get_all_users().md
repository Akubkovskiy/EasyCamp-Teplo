---
source_file: "app\telegram\auth\admin.py"
type: "code"
community: "cleaner_task_flow.py / get_all_users()"
location: "L110"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/cleaner_task_flow.py_/_get_all_users()
---

# get_all_users()

## Connections
- [[_notify_admins()]] - `calls` [INFERRED]
- [[_notify_admins_supply_alert()]] - `calls` [INFERRED]
- [[_send_admin_booking_notification()]] - `calls` [INFERRED]
- [[_send_pay_receipt_to_admins()]] - `calls` [INFERRED]
- [[admin.py]] - `contains` [EXTRACTED]
- [[cleaner_claim_submit()]] - `calls` [INFERRED]
- [[decline_cleaning()]] - `calls` [INFERRED]
- [[guest_cancel_confirm()]] - `calls` [INFERRED]
- [[guest_feedback_message()]] - `calls` [INFERRED]
- [[show_users_list()]] - `calls` [INFERRED]
- [[Возвращает всех пользователей из БД]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/cleaner_task_flow.py_/_get_all_users()