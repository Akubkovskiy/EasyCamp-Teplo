---
source_file: "app\services\pricing_service.py"
type: "code"
community: "BookingStatus / Booking"
location: "L10"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# PricingService

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[EditHouseStates]] - `uses` [INFERRED]
- [[Entry гость нажал «Забронировать» в карточке домика.]] - `uses` [INFERRED]
- [[Filter contact share только от гостей в pending booking flow.     Если фильтр н]] - `uses` [INFERRED]
- [[Filter гость находится в режиме ожидания чека (нажал «Отправить чек»).]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[HouseDiscount]] - `uses` [INFERRED]
- [[HousePrice]] - `uses` [INFERRED]
- [[HousePriceCalendarEntry]] - `uses` [INFERRED]
- [[HousePublicOut]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[HouseStates]] - `uses` [INFERRED]
- [[Match `guestbookdigits` strictly. Excludes guests, confirm,     cancel,]] - `uses` [INFERRED]
- [[PDF  любая выписка из банка как document. Принимаем pdfjpegpng по     `mime_]] - `uses` [INFERRED]
- [[PriceStates]] - `uses` [INFERRED]
- [[Self-service бронирование гостя (Phase G10.1).  Гость 1) выбирает даты через `g]] - `uses` [INFERRED]
- [[pricing_service.py]] - `contains` [EXTRACTED]
- [[Админ отклоняет бронь - CANCELLED + notify guest.]] - `uses` [INFERRED]
- [[Админ подтверждает бронь - CONFIRMED + notify guest.]] - `uses` [INFERRED]
- [[Возврат в главное меню (витрина или кабинет).]] - `uses` [INFERRED]
- [[Возвращает (name, phone) из User, если уже сохранён.]] - `uses` [INFERRED]
- [[Выбрано кол-во гостей - показ карточки подтверждения.]] - `uses` [INFERRED]
- [[Гость нажал «Отменить бронь» проверяем окно отмены, спрашиваем подтверждение.]] - `uses` [INFERRED]
- [[Детальная карточка домика с фото]] - `uses` [INFERRED]
- [[Кнопки выбора кол-ва гостей в пределах вместимости домика.]] - `uses` [INFERRED]
- [[Кнопки для случая «слишком близко к заезду» — гость не может     отменить сам, п]] - `uses` [INFERRED]
- [[Команда about — О базе отдыха.]] - `uses` [INFERRED]
- [[Команда booking — Моя бронь.]] - `uses` [INFERRED]
- [[Команда contact — Связаться с нами.]] - `uses` [INFERRED]
- [[Команда dates — проверить свободные даты (запускает availability flow).]] - `uses` [INFERRED]
- [[Команда location — Где мы находимся.]] - `uses` [INFERRED]
- [[Команда login — Авторизоваться по брони.]] - `uses` [INFERRED]
- [[Контакт получен в self-service потоке (не login). Создаём User     с ролью GUEST]] - `uses` [INFERRED]
- [[Обработка контакта для входа]] - `uses` [INFERRED]
- [[Обработчик выбора даты выезда]] - `uses` [INFERRED]
- [[Обработчик выбора даты заезда]] - `uses` [INFERRED]
- [[Обработчик команды availability для проверки доступности домиков]] - `uses` [INFERRED]
- [[Общая логика admin approve задаток или полная оплата.      full_payment=False]] - `uses` [INFERRED]
- [[Общая логика для photo и document уведомить админов с inline-кнопками     зада]] - `uses` [INFERRED]
- [[Парсит AVITO_ITEM_IDS из настроек.     Формат avito_item_idhouse_id,avito_it]] - `uses` [INFERRED]
- [[Переключение месяца при выборе даты выезда]] - `uses` [INFERRED]
- [[Периодические задачи ценообразования 1. Авто-скидки на свободные даты (горящие]] - `uses` [INFERRED]
- [[Подтверждение отмены — фактически отменяет бронь и нотифицирует админа.]] - `uses` [INFERRED]
- [[Показывает меню гостя витрина (unauth) или кабинет (auth).]] - `uses` [INFERRED]
- [[Полный цикл сначала проверяем скидки, потом синхронизируем цены на Авито.]] - `uses` [INFERRED]
- [[Помощник ищет актуальную бронь для пользователя.      Приоритет     1) Теку]] - `uses` [INFERRED]
- [[Прайс-календарь для конкретного домика (для виджета на сайте).]] - `uses` [INFERRED]
- [[Проверяет загруженность на ближайшие дни.     Если домик свободен завтрапослез]] - `uses` [INFERRED]
- [[Публичный API для домиков и цен. Используется сайтом teplo-v-arkhyze для отобра]] - `uses` [INFERRED]
- [[Расчёт стоимости проживания (для формы бронирования на сайте).]] - `uses` [INFERRED]
- [[Расчёт цен с учётом сезонности и скидок.]] - `rationale_for` [EXTRACTED]
- [[Сервис синхронизации цен с Avito. Берёт цены из базы (base_price + сезонные + с]] - `uses` [INFERRED]
- [[Синхронизирует текущие цены (base + сезонные + скидки) на Авито.     Запускаетс]] - `uses` [INFERRED]
- [[Синхронизирует цены из базы на Авито.      Args         db Сессия БД]] - `uses` [INFERRED]
- [[Список домиков с текущими ценами (для сайта).]] - `uses` [INFERRED]
- [[Список сезонных цен для домика]] - `uses` [INFERRED]
- [[Уведомление админам с кнопками confirmreject.]] - `uses` [INFERRED]
- [[Финальное подтверждение - Booking(NEW) + admin notification.]] - `uses` [INFERRED]
- [[Шлём гостю экран с выбором кол-ва гостей.     Принимаем либо CallbackQuery (edit]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking