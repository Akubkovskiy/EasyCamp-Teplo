---
source_file: "app\services\global_settings.py"
type: "rationale"
community: "guest.py / safe_edit()"
location: "L115"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/guest.py_/_safe_edit()
---

# % от total_price, который гость вносит как задаток при бронировании.     Остаток

## Connections
- [[GlobalSetting]] - `uses` [INFERRED]
- [[get_guest_advance_percent()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/guest.py_/_safe_edit()