---
source_file: "app\telegram\handlers\guest.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L1056"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Общая логика для photo и document: уведомить админов с inline-кнопками     зада

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[GlobalSetting]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[_send_pay_receipt_to_admins()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking