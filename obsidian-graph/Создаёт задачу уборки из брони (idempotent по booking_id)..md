---
source_file: "app\services\cleaning_task_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L65"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Создаёт задачу уборки из брони (idempotent по booking_id).

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[CleaningPaymentEntryType]] - `uses` [INFERRED]
- [[CleaningPaymentLedger]] - `uses` [INFERRED]
- [[CleaningRate]] - `uses` [INFERRED]
- [[CleaningTask]] - `uses` [INFERRED]
- [[CleaningTaskCheck]] - `uses` [INFERRED]
- [[CleaningTaskMedia]] - `uses` [INFERRED]
- [[CleaningTaskStatus]] - `uses` [INFERRED]
- [[PaymentStatus]] - `uses` [INFERRED]
- [[SupplyAlert]] - `uses` [INFERRED]
- [[SupplyAlertStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking