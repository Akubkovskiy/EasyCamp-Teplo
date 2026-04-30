---
source_file: "app\models.py"
type: "code"
community: "BookingStatus / Booking"
location: "L260"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# SupplyAlert

## Connections
- [[Base_1]] - `inherits` [EXTRACTED]
- [[Base]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[cancel_booking должен     - перевести task в CANCELLED     - погасить cleaning_]] - `uses` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[open_supply_alert()]] - `calls` [INFERRED]
- [[Если задача ещё в IN_PROGRESS  PENDING  ACCEPTED — cancel должен     перевести]] - `uses` [INFERRED]
- [[Начисляет сдельную оплату за уборку по тарифу домика.]] - `uses` [INFERRED]
- [[Открывает (или возвращает существующий) `SupplyAlert` для задачи.         Idemp]] - `uses` [INFERRED]
- [[Помечает активные `SupplyAlert` задачи как RESOLVED.         Возвращает количес]] - `uses` [INFERRED]
- [[Сервис задач уборки + первичный расчёт начислений.]] - `uses` [INFERRED]
- [[Создаёт задачу уборки из брони (idempotent по booking_id).]] - `uses` [INFERRED]
- [[Тесты Phase C10 (cleaner hardening) accrual, supply_alert, booking cancel propa]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking