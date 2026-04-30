---
source_file: "app\models.py"
type: "code"
community: "BookingStatus / Booking"
location: "L174"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# CleaningTaskStatus

## Connections
- [[Base]] - `uses` [INFERRED]
- [[Best-effort уведомление уборщицы об отмене связанной задачи.]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[CleaningTaskService]] - `uses` [INFERRED]
- [[Enum]] - `inherits` [EXTRACTED]
- [[Filter только фото с caption `taskN`. Без этого фильтра handler     проглатыв]] - `uses` [INFERRED]
- [[Read guest contact fields from either nested contact data or legacy top-level pa]] - `uses` [INFERRED]
- [[Replace only empty or placeholder values with a better Avito contact value.]] - `uses` [INFERRED]
- [[Safe wrapper for background sheets sync.         Catches and logs all errors to]] - `uses` [INFERRED]
- [[Smoke verification for Cleaner v2 flow.  Checks 1) task completion is blocke]] - `uses` [INFERRED]
- [[cancel_booking должен     - перевести task в CANCELLED     - погасить cleaning_]] - `uses` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[str]] - `inherits` [EXTRACTED]
- [[Блокировка дат в Avito для брони]] - `uses` [INFERRED]
- [[Если задача ещё в IN_PROGRESS  PENDING  ACCEPTED — cancel должен     перевести]] - `uses` [INFERRED]
- [[Находит связанную CleaningTask и переводит её в CANCELLED.         Активные cle]] - `uses` [INFERRED]
- [[Начисляет сдельную оплату за уборку по тарифу домика.]] - `uses` [INFERRED]
- [[Обновление существующего бронирования.]] - `uses` [INFERRED]
- [[Открывает (или возвращает существующий) `SupplyAlert` для задачи.         Idemp]] - `uses` [INFERRED]
- [[Отмена брони. Каскадно отменяет связанную CleaningTask и         активные начис]] - `uses` [INFERRED]
- [[Полное удаление брони из базы данных.         ВНИМАНИЕ Это действие необратимо]] - `uses` [INFERRED]
- [[Получить бронь по ID с информацией о доме]] - `uses` [INFERRED]
- [[Получить список доступных домов на указанные даты.]] - `uses` [INFERRED]
- [[Помечает активные `SupplyAlert` задачи как RESOLVED.         Возвращает количес]] - `uses` [INFERRED]
- [[Проверка доступности дат.         Возвращает True если даты свободны.]] - `uses` [INFERRED]
- [[Разблокировка дат в Avito при отменеудалении брони.                  Для Авит]] - `uses` [INFERRED]
- [[Сервис бизнес-логики для бронирований]] - `uses` [INFERRED]
- [[Сервис задач уборки + первичный расчёт начислений.]] - `uses` [INFERRED]
- [[Синхронизация всех броней с Google Sheets.         Raises exception on failure]] - `uses` [INFERRED]
- [[Создание новой брони.]] - `uses` [INFERRED]
- [[Создать или обновить бронь из Avito webhook.]] - `uses` [INFERRED]
- [[Создаёт задачу уборки из брони (idempotent по booking_id).]] - `uses` [INFERRED]
- [[Тесты Phase C10 (cleaner hardening) accrual, supply_alert, booking cancel propa]] - `uses` [INFERRED]
- [[Шлёт всем админам уведомление о новом SupplyAlert.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking