---
source_file: "app\services\avito_api_service.py"
type: "rationale"
community: "AvitoAPIService / .ensure_token()"
location: "L668"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/AvitoAPIService_/_.ensure_token()
---

# Получить текущий прайс-календарь с Avito.          Args:             item_id:

## Connections
- [[.get_price_calendar()]] - `rationale_for` [EXTRACTED]
- [[BookingStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/EXTRACTED #community/AvitoAPIService_/_.ensure_token()