---
source_file: "app\services\avito_sync_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L301"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Синхронизация всех объявлений Avito      Args:         item_house_mapping: Сл

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[sync_all_avito_items()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking