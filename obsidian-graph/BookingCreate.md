---
source_file: "app\schemas\booking.py"
type: "code"
community: "BookingStatus / Booking"
location: "L23"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# BookingCreate

## Connections
- [[Best-effort уведомление уборщицы об отмене связанной задачи.]] - `uses` [INFERRED]
- [[BookingBase]] - `inherits` [EXTRACTED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[Entry гость нажал «Забронировать» в карточке домика.]] - `uses` [INFERRED]
- [[Filter contact share только от гостей в pending booking flow.     Если фильтр н]] - `uses` [INFERRED]
- [[HouseOut]] - `uses` [INFERRED]
- [[Match `guestbookdigits` strictly. Excludes guests, confirm,     cancel,]] - `uses` [INFERRED]
- [[Read guest contact fields from either nested contact data or legacy top-level pa]] - `uses` [INFERRED]
- [[Replace only empty or placeholder values with a better Avito contact value.]] - `uses` [INFERRED]
- [[Safe wrapper for background sheets sync.         Catches and logs all errors to]] - `uses` [INFERRED]
- [[Self-service бронирование гостя (Phase G10.1).  Гость 1) выбирает даты через `g]] - `uses` [INFERRED]
- [[Site lead intake endpoint (Phase S10.1).  Принимает заявки с публичного сайта `t]] - `uses` [INFERRED]
- [[SiteLeadCreate]] - `uses` [INFERRED]
- [[SiteLeadOut]] - `uses` [INFERRED]
- [[booking.py]] - `contains` [EXTRACTED]
- [[create_booking()]] - `calls` [INFERRED]
- [[create_booking()_1]] - `calls` [INFERRED]
- [[create_site_lead()]] - `calls` [INFERRED]
- [[guest_book_confirm()]] - `calls` [INFERRED]
- [[Авторизация по статичному токену. Если в окружении токен пуст —     endpoint счи]] - `uses` [INFERRED]
- [[Админ отклоняет бронь - CANCELLED + notify guest.]] - `uses` [INFERRED]
- [[Админ подтверждает бронь - CONFIRMED + notify guest.]] - `uses` [INFERRED]
- [[Блокировка дат в Avito для брони]] - `uses` [INFERRED]
- [[Возвращает (house_id, fallback_note). Стратегия     1. Явный id — берём, если H]] - `uses` [INFERRED]
- [[Возвращает (name, phone) из User, если уже сохранён.]] - `uses` [INFERRED]
- [[Выбрано кол-во гостей - показ карточки подтверждения.]] - `uses` [INFERRED]
- [[Гость нажал «Отменить бронь» проверяем окно отмены, спрашиваем подтверждение.]] - `uses` [INFERRED]
- [[Заявка с сайта. Минимальный набор полей чтобы создать `Booking`.]] - `uses` [INFERRED]
- [[Кнопки выбора кол-ва гостей в пределах вместимости домика.]] - `uses` [INFERRED]
- [[Кнопки для случая «слишком близко к заезду» — гость не может     отменить сам, п]] - `uses` [INFERRED]
- [[Контакт получен в self-service потоке (не login). Создаём User     с ролью GUEST]] - `uses` [INFERRED]
- [[Находит связанную CleaningTask и переводит её в CANCELLED.         Активные cle]] - `uses` [INFERRED]
- [[Обновление бронирования.]] - `uses` [INFERRED]
- [[Обновление существующего бронирования.]] - `uses` [INFERRED]
- [[Обработка создания бронирования.]] - `uses` [INFERRED]
- [[Ответ для site API. lead_id == Booking.id.]] - `uses` [INFERRED]
- [[Отмена брони. Каскадно отменяет связанную CleaningTask и         активные начис]] - `uses` [INFERRED]
- [[Подтверждение отмены — фактически отменяет бронь и нотифицирует админа.]] - `uses` [INFERRED]
- [[Полное удаление брони из базы данных.         ВНИМАНИЕ Это действие необратимо]] - `uses` [INFERRED]
- [[Получить бронь по ID с информацией о доме]] - `uses` [INFERRED]
- [[Получить список доступных домов на указанные даты.]] - `uses` [INFERRED]
- [[Проверка доступности дат.         Возвращает True если даты свободны.]] - `uses` [INFERRED]
- [[Просмотр деталей бронирования.]] - `uses` [INFERRED]
- [[Разблокировка дат в Avito при отменеудалении брони.                  Для Авит]] - `uses` [INFERRED]
- [[Сервис бизнес-логики для бронирований]] - `uses` [INFERRED]
- [[Синхронизация всех броней с Google Sheets.         Raises exception on failure]] - `uses` [INFERRED]
- [[Создание новой брони.]] - `uses` [INFERRED]
- [[Создать или обновить бронь из Avito webhook.]] - `uses` [INFERRED]
- [[Список всех бронирований.]] - `uses` [INFERRED]
- [[Страница создания нового бронирования.]] - `uses` [INFERRED]
- [[Уведомление админам с кнопками confirmreject.]] - `uses` [INFERRED]
- [[Финальное подтверждение - Booking(NEW) + admin notification.]] - `uses` [INFERRED]
- [[Форматирует телефон в вид +7 (XXX) XXX-XX-XX]] - `uses` [INFERRED]
- [[Шлём гостю экран с выбором кол-ва гостей.     Принимаем либо CallbackQuery (edit]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking