---
source_file: "app\services\global_settings.py"
type: "code"
community: "GlobalSetting / global_settings.py"
location: "L94"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/GlobalSetting_/_global_settings.py
---

# can_guest_self_cancel()

## Connections
- [[Pure-функция для тестов гость может сам отменить бронь, только     если до заез]] - `rationale_for` [EXTRACTED]
- [[global_settings.py]] - `contains` [EXTRACTED]
- [[guest_cancel_confirm()]] - `calls` [INFERRED]
- [[guest_cancel_start()]] - `calls` [INFERRED]
- [[test_cancel_inside_window_blocked()]] - `calls` [INFERRED]
- [[test_cancel_outside_window_allowed()]] - `calls` [INFERRED]
- [[test_cancel_window_zero_means_never_self_cancel_for_today()]] - `calls` [INFERRED]
- [[test_cancel_zero_days_blocked()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/GlobalSetting_/_global_settings.py