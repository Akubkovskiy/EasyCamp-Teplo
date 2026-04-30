---
source_file: "app\telegram\handlers\guest.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L262"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Команда /booking — Моя бронь.

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[GlobalSetting]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[cmd_booking()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking