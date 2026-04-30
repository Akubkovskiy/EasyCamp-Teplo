---
source_file: "app\services\avito_price_service.py"
type: "rationale"
community: "str / settings.py"
location: "L21"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/str_/_settings.py
---

# Парсит AVITO_ITEM_IDS из настроек.     Формат: "avito_item_id:house_id,avito_it

## Connections
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[parse_avito_item_ids()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/str_/_settings.py