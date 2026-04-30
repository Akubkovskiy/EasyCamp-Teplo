---
source_file: "app\services\avito_price_service.py"
type: "rationale"
community: "str / settings.py"
location: "L1"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/str_/_settings.py
---

# Сервис синхронизации цен с Avito. Берёт цены из базы (base_price + сезонные + с

## Connections
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[avito_price_service.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/str_/_settings.py