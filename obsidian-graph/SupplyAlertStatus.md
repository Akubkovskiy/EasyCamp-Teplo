---
source_file: "app\models.py"
type: "code"
community: "BookingStatus / Booking"
location: "L254"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# SupplyAlertStatus

## Connections
- [[Base]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[Enum]] - `inherits` [EXTRACTED]
- [[cancel_booking должен     - перевести task в CANCELLED     - погасить cleaning_]] - `uses` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[str]] - `inherits` [EXTRACTED]
- [[Если задача ещё в IN_PROGRESS  PENDING  ACCEPTED — cancel должен     перевести]] - `uses` [INFERRED]
- [[Начисляет сдельную оплату за уборку по тарифу домика.]] - `uses` [INFERRED]
- [[Открывает (или возвращает существующий) `SupplyAlert` для задачи.         Idemp]] - `uses` [INFERRED]
- [[Помечает активные `SupplyAlert` задачи как RESOLVED.         Возвращает количес]] - `uses` [INFERRED]
- [[Сервис задач уборки + первичный расчёт начислений.]] - `uses` [INFERRED]
- [[Создаёт задачу уборки из брони (idempotent по booking_id).]] - `uses` [INFERRED]
- [[Тесты Phase C10 (cleaner hardening) accrual, supply_alert, booking cancel propa]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking