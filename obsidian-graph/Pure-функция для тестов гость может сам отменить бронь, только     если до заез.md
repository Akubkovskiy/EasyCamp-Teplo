---
source_file: "app\services\global_settings.py"
type: "rationale"
community: "GlobalSetting / global_settings.py"
location: "L95"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/GlobalSetting_/_global_settings.py
---

# Pure-функция для тестов: гость может сам отменить бронь, только     если до заез

## Connections
- [[GlobalSetting]] - `uses` [INFERRED]
- [[can_guest_self_cancel()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/GlobalSetting_/_global_settings.py