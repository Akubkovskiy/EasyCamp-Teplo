---
source_file: "app\services\global_settings.py"
type: "rationale"
community: "GlobalSetting / global_settings.py"
location: "L50"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/GlobalSetting_/_global_settings.py
---

# Idempotent upsert. Caller отвечает за commit.

## Connections
- [[GlobalSetting]] - `uses` [INFERRED]
- [[set_value()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/GlobalSetting_/_global_settings.py