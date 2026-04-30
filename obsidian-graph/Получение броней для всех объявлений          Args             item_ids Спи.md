---
source_file: "app\services\avito_api_service.py"
type: "rationale"
community: "AvitoAPIService / .ensure_token()"
location: "L151"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/AvitoAPIService_/_.ensure_token()
---

# Получение броней для всех объявлений          Args:             item_ids: Спи

## Connections
- [[.get_all_bookings()]] - `rationale_for` [EXTRACTED]
- [[BookingStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/EXTRACTED #community/AvitoAPIService_/_.ensure_token()