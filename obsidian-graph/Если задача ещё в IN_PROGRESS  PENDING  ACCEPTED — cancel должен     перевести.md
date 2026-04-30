---
source_file: "tests\test_cleaner_hardening.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L272"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Если задача ещё в IN_PROGRESS / PENDING / ACCEPTED — cancel должен     перевести

## Connections
- [[Base]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[CleaningPaymentEntryType]] - `uses` [INFERRED]
- [[CleaningPaymentLedger]] - `uses` [INFERRED]
- [[CleaningRate]] - `uses` [INFERRED]
- [[CleaningTask]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[CleaningTaskStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[PaymentStatus]] - `uses` [INFERRED]
- [[SupplyAlert]] - `uses` [INFERRED]
- [[SupplyAlertStatus]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[test_booking_cancel_propagates_to_active_task()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking