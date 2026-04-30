---
source_file: "app\telegram\handlers\guest.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L240"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Команда /contact — Связаться с нами.

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[GlobalSetting]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[cmd_contact()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking