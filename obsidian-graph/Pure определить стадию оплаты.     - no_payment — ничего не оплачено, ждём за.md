---
source_file: "app\services\global_settings.py"
type: "rationale"
community: "GlobalSetting / global_settings.py"
location: "L135"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/GlobalSetting_/_global_settings.py
---

# Pure: определить стадию оплаты.     - "no_payment" — ничего не оплачено, ждём за

## Connections
- [[GlobalSetting]] - `uses` [INFERRED]
- [[payment_stage()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/GlobalSetting_/_global_settings.py