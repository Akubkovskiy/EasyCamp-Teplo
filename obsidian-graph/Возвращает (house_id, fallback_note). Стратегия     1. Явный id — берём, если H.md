---
source_file: "app\api\site_leads.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L111"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Возвращает (house_id, fallback_note). Стратегия:     1. Явный id — берём, если H

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingCreate]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[_resolve_house_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking