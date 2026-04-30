---
source_file: "app\models.py"
type: "code"
community: "BookingStatus / Booking"
location: "L144"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# UserRole

## Connections
- [[AuthRedirectException]] - `uses` [INFERRED]
- [[Base]] - `uses` [INFERRED]
- [[Custom exception for authentication redirects in web routes]] - `uses` [INFERRED]
- [[Dependency to get current admin user from cookie session.     Redirects to adm]] - `uses` [INFERRED]
- [[Entry гость нажал «Забронировать» в карточке домика.]] - `uses` [INFERRED]
- [[Enum]] - `inherits` [EXTRACTED]
- [[Filter contact share только от гостей в pending booking flow.     Если фильтр н]] - `uses` [INFERRED]
- [[Filter только фото с caption `taskN`. Без этого фильтра handler     проглатыв]] - `uses` [INFERRED]
- [[Match `guestbookdigits` strictly. Excludes guests, confirm,     cancel,]] - `uses` [INFERRED]
- [[NotificationRule]] - `uses` [INFERRED]
- [[NotificationService]] - `uses` [INFERRED]
- [[Same as above but redirects to login page on failure.     Used for page routes.]] - `uses` [INFERRED]
- [[Self-service бронирование гостя (Phase G10.1).  Гость 1) выбирает даты через `g]] - `uses` [INFERRED]
- [[Site lead intake endpoint (Phase S10.1).  Принимает заявки с публичного сайта `t]] - `uses` [INFERRED]
- [[SiteLeadCreate]] - `uses` [INFERRED]
- [[SiteLeadOut]] - `uses` [INFERRED]
- [[Smoke verification for Cleaner v2 flow.  Checks 1) task completion is blocke]] - `uses` [INFERRED]
- [[UserAddStates]] - `uses` [INFERRED]
- [[cancel_booking должен     - перевести task в CANCELLED     - погасить cleaning_]] - `uses` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[str]] - `inherits` [EXTRACTED]
- [[Авторизация по статичному токену. Если в окружении токен пуст —     endpoint счи]] - `uses` [INFERRED]
- [[Админ отклоняет бронь - CANCELLED + notify guest.]] - `uses` [INFERRED]
- [[Админ подтверждает бронь - CONFIRMED + notify guest.]] - `uses` [INFERRED]
- [[Возвращает (house_id, fallback_note). Стратегия     1. Явный id — берём, если H]] - `uses` [INFERRED]
- [[Возвращает (name, phone) из User, если уже сохранён.]] - `uses` [INFERRED]
- [[Возвращает PK `users.id` по `telegram_id`. Используется для записи     в FK-кол]] - `uses` [INFERRED]
- [[Возвращает всех пользователей из БД]] - `uses` [INFERRED]
- [[Возвращает имя пользователя из БД]] - `uses` [INFERRED]
- [[Выбрано кол-во гостей - показ карточки подтверждения.]] - `uses` [INFERRED]
- [[Гость нажал «Отменить бронь» проверяем окно отмены, спрашиваем подтверждение.]] - `uses` [INFERRED]
- [[Добавляет пользователя в БД и обновляет кеш]] - `uses` [INFERRED]
- [[Если задача ещё в IN_PROGRESS  PENDING  ACCEPTED — cancel должен     перевести]] - `uses` [INFERRED]
- [[Заявка с сайта. Минимальный набор полей чтобы создать `Booking`.]] - `uses` [INFERRED]
- [[Кнопки выбора кол-ва гостей в пределах вместимости домика.]] - `uses` [INFERRED]
- [[Кнопки для случая «слишком близко к заезду» — гость не может     отменить сам, п]] - `uses` [INFERRED]
- [[Контакт получен в self-service потоке (не login). Создаём User     с ролью GUEST]] - `uses` [INFERRED]
- [[Меню управления пользователями]] - `uses` [INFERRED]
- [[Начало добавления пользователя]] - `uses` [INFERRED]
- [[Обновляет кеш пользователей из БД]] - `uses` [INFERRED]
- [[Обработка ID пользователя]] - `uses` [INFERRED]
- [[Обработка входа.      Сначала пробуем env-fallback (`ADMIN_WEB_USERNAME`  `AD]] - `uses` [INFERRED]
- [[Обработка имени и сохранение]] - `uses` [INFERRED]
- [[Ответ для site API. lead_id == Booking.id.]] - `uses` [INFERRED]
- [[Отправить уборщицам список задач на завтра с переходом в карточку.]] - `uses` [INFERRED]
- [[Подтверждение отмены — фактически отменяет бронь и нотифицирует админа.]] - `uses` [INFERRED]
- [[Показать список пользователей определенной роли]] - `uses` [INFERRED]
- [[Получает админов из переменных окружения]] - `uses` [INFERRED]
- [[Проверка секрета и старт сессии]] - `uses` [INFERRED]
- [[Проверяет, является ли пользователь авторизованным гостем]] - `uses` [INFERRED]
- [[Проверяет, является ли пользователь уборщицей]] - `uses` [INFERRED]
- [[Сервис для рассылки уведомлений по правилам]] - `uses` [INFERRED]
- [[Создание админа и Завершение]] - `uses` [INFERRED]
- [[Создатьобновить задачи уборки по выездам на завтра.]] - `uses` [INFERRED]
- [[Сохранение шага 1 - Переход к Шагу 2]] - `uses` [INFERRED]
- [[Сохранение шага 2 - Завершение]] - `uses` [INFERRED]
- [[Страница входа в админ-панель]] - `uses` [INFERRED]
- [[Тесты Phase C10 (cleaner hardening) accrual, supply_alert, booking cancel propa]] - `uses` [INFERRED]
- [[Уведомление админам с кнопками confirmreject.]] - `uses` [INFERRED]
- [[Удаление пользователя]] - `uses` [INFERRED]
- [[Удаляет ТОЛЬКО гостя (без риска снести админауборщицу).]] - `uses` [INFERRED]
- [[Удаляет пользователя из БД и обновляет кеш]] - `uses` [INFERRED]
- [[Финальное подтверждение - Booking(NEW) + admin notification.]] - `uses` [INFERRED]
- [[Шаг 1 Идентичность проекта]] - `uses` [INFERRED]
- [[Шаг 3 Создание Администратора]] - `uses` [INFERRED]
- [[Шлём гостю экран с выбором кол-ва гостей.     Принимаем либо CallbackQuery (edit]] - `uses` [INFERRED]
- [[Шлёт всем админам уведомление о новом SupplyAlert.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking