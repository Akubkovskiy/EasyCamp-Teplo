---
source_file: "app\telegram\handlers\cleaner_expenses.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L37"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Filter: только фото с caption в формате `claim task=N amount=X items=...`.

## Connections
- [[CleaningPaymentEntryType]] - `uses` [INFERRED]
- [[CleaningPaymentLedger]] - `uses` [INFERRED]
- [[PaymentStatus]] - `uses` [INFERRED]
- [[SupplyClaimStatus]] - `uses` [INFERRED]
- [[SupplyExpenseClaim]] - `uses` [INFERRED]
- [[_is_cleaner_claim_photo()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking