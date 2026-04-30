---
source_file: "app\services\avito_api_service.py"
type: "rationale"
community: "AvitoAPIService / .ensure_token()"
location: "L175"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/AvitoAPIService_/_.ensure_token()
---

# Блокировка дат в календаре Avito          Args:             item_id: ID объяв

## Connections
- [[.block_dates()]] - `rationale_for` [EXTRACTED]
- [[BookingStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/EXTRACTED #community/AvitoAPIService_/_.ensure_token()