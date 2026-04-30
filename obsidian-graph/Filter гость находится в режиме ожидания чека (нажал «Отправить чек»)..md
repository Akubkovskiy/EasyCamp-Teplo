---
source_file: "app\telegram\handlers\guest.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L1043"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Filter: гость находится в режиме ожидания чека (нажал «Отправить чек»).

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[GlobalSetting]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[_is_pay_receipt_waiting()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking