---
source_file: "app\services\avito_api_service.py"
type: "rationale"
community: "AvitoAPIService / .ensure_token()"
location: "L131"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/AvitoAPIService_/_.ensure_token()
---

# Получение броней за период (от сегодня вперед)          Args:             ite

## Connections
- [[.get_bookings_for_period()]] - `rationale_for` [EXTRACTED]
- [[BookingStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/EXTRACTED #community/AvitoAPIService_/_.ensure_token()