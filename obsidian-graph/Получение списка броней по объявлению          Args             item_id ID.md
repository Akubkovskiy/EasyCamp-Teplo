---
source_file: "app\services\avito_api_service.py"
type: "rationale"
community: "AvitoAPIService / .ensure_token()"
location: "L84"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/AvitoAPIService_/_.ensure_token()
---

# Получение списка броней по объявлению          Args:             item_id: ID

## Connections
- [[.get_bookings()]] - `rationale_for` [EXTRACTED]
- [[BookingStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/EXTRACTED #community/AvitoAPIService_/_.ensure_token()