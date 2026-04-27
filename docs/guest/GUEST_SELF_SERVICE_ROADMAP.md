# Guest Self-Service Roadmap (Phase G10..G12)

Статус: **ACTIVE** — на разработку\
Дата: 2026-04-27\
Автор: claude-code\
Основа: `docs/guest/VIBECODE_ROADMAP_GUEST_V2.md` (G0..G9 MVP закрыт)\
Цель: довести роль "Гость" до состояния, в котором бота можно отдавать гостям без ручного сопровождения админом — поиск, бронирование, оплата, отмена, поддержка проходят полностью через бота.

---

## 0. Контекст

### Что уже сделано (Guest V2 MVP)

- Витрина `unauth` (О базе / Домики / Даты / FAQ / Где мы / Связь / Авторизоваться)
- Авторизация через `request_contact` + точный матч телефона
- Личный кабинет: `Моя бронь`, инструкция (24ч gate), Wi-Fi, правила, поддержка
- Оплата (MVP): фото чека -&gt; admin approve/reject -&gt; бронь становится `PAID`
- FAQ structured form, партнёры v1 (текстовый каталог), feature flags

### Что блокирует "отдать бота гостям"

1. Нет self-service создания брони. Сейчас `booking:create:{house_id}` разворачивается в админский FSM, где нужно вручную ввести имя/телефон. Гость не может сам забронировать.
2. Нет возможности отменить бронь. `docs/roles/guest_role.md` это описывает, но в коде кнопки нет.
3. Time-gates захардкожены (24ч), окно отмены не сконфигурировано.

---

## 1. Phase G10 — Self-Service MVP (сегодня)

Цель фазы: гость может полностью пройти цикл booking → payment → cancel внутри бота. Оплата на этом этапе остаётся как фото чека + admin approve (Robokassa отложена в G11).

### G10.1 — Self-service booking flow

- \[ \] Новый callback `guest:book:{house_id}` (отдельный от админского `booking:create:`).
- \[ \] Если гость авторизован (`is_guest_authorized(user_id)`) — берём `guest_name` и `guest_phone` из `User`. Не спрашиваем повторно.
- \[ \] Если гость не авторизован — внутри потока запрашиваем контакт через `request_contact_keyboard()`. После share contact: создаём/обновляем `User` с ролью `GUEST`, продолжаем поток.
- \[ \] Шаги: дата заезда -&gt; дата выезда (из существующего availability flow) -&gt; подтверждение карточки -&gt; create `Booking(status=NEW, source=telegram)`.
- \[ \] Успех: гостю показывается карточка брони + reply "ждите подтверждения админом". Админу — уведомление с кнопками `Подтвердить` / `Отклонить`.
- \[ \] Admin confirm -&gt; `status=CONFIRMED`, гостю notify + ссылка/реквизиты на оплату.
- \[ \] Admin reject -&gt; `status=CANCELLED` (или новый `REJECTED`), гостю notify с указанием причины.
- \[ \] Гард на занятые даты: `BookingService.check_availability` в момент создания.
- \[ \] Гард на дублирование: один активный `NEW`/`CONFIRMED` per (telegram_id, house, dates).

### G10.2 — Cancel booking

- \[ \] Кнопка `🚫 Отменить бронь` в карточке `guest:my_booking`.
- \[ \] Если до заезда &gt; `guest_cancel_window_days` дней (default 7) — гость отменяет сам:
  - подтверждение через inline-кнопки `Да, отменить` / `Нет`
  - на confirm: `status=CANCELLED`, `cancelled_by='guest'`, audit-запись
  - админу — уведомление (без действия)
  - гостю — подтверждение
- \[ \] Если до заезда ≤ N дней — экран "Свяжитесь с админом, возможен штраф" + кнопка перехода в чат админа.

### G10.3 — Hardening / конфиги

- \[ \] `GlobalSetting` ключи:
  - `guest_cancel_window_days` (int, default 7)
  - `guest_instruction_open_hours` (int, default 24) — закрывает items "G5: вынести окно доступа в конфиг"
- \[ \] Helper `app/services/global_settings.py` или существующий — обертка с дефолтами.
- \[ \] Тесты: phone matching уже есть, добавить unit на cancel window decision и time-gate decision.

### G10.4 — UAT

- \[ \] Прогнать `docs/guest/GUEST_V2_UAT_CHECKLIST.md` целиком.
- \[ \] Дополнительные пункты:
  - \[ \] Self-service book с unauth: контакт → имя из User → бронь создана → админ подтвердил
  - \[ \] Self-service book с auth: бронь создана сразу, имя/телефон не спрашивает повторно
  - \[ \] Бронь на занятые даты — отказ
  - \[ \] Cancel &gt;N дней — отменяется сам
  - \[ \] Cancel ≤N дней — отправляет к админу
  - \[ \] Time-gate инструкции корректно использует `guest_instruction_open_hours`

### Definition of Done G10

- Гость без участия админа может: посмотреть домики, выбрать даты, создать бронь, дождаться confirm, прислать чек, дождаться approve, попасть в кабинет, открыть инструкцию по таймеру, отменить бронь (если успел), задать вопрос. Всё это — через бота.
- Админ участвует только как модератор (confirm / approve / reject).

---

## 2. Phase G11 — Auto-payment (Robokassa)

Цель: убрать ручной admin approve из цикла оплаты. Гость нажал «Оплатить» → дошёл до оплаты на стороне Robokassa → webhook → бронь автоматически `PAID`.

### G11.1 — `GuestPaymentClaim` ledger

- Таблица для аудита платежей (закрывает open-item из G4).
- Поля: id, booking_id, provider (`robokassa` / `manual_receipt`), amount, status (`pending` / `success` / `failed` / `refunded`), provider_invoice_id, raw_payload (JSON), created_at, updated_at.

### G11.2 — Robokassa интеграция

- Reuse подход из vpn-orchestrator (`vpn-orchestrator/docs/robokassa-comet-brief.md`).
- Сервис: `app/services/robokassa_service.py` — генерация invoice URL, верификация ResultURL signature.
- Webhook: `app/api/payments_robokassa.py`.
- Хендлер `guest:pay:robokassa` -&gt; отдаёт ссылку, по success-callback -&gt; `PaymentService.mark_paid`.

### G11.3 — Feature flag и UX

- `GUEST_FEATURE_AUTOPAY` (default `false` пока проверяем).
- Если включено — кнопка "💳 Оплатить онлайн" появляется первой; "📸 Отправить чек" остаётся как fallback.

### Definition of Done G11

- В `RECEIPT_GREEN` включаем autopay в проде, гость закрывает оплату без админа в &gt; 90% случаев.

---

## 3. Phase G12 — SaaS Finish

Закрываем оставшиеся open-items из Guest V2 + готовим под second tenant.

### G12.1 — Меню/тексты в DB

- Перенести порядок и подписи кнопок гостя в `GlobalSetting` или новую таблицу `GuestMenuConfig`.
- Закрывает open-item G8 ("вынести порядок меню/тексты кнопок в DB-конфиг").

### G12.2 — Партнёры v2

- Структурные карточки в БД: `partners`, `partner_categories`, `partner_offers`, `partner_leads`.
- Закрывает open-item G7.

### G12.3 — Расширенный feedback

- Добавить медиа + статусы обработки + приоритет.
- Закрывает open-item G6.

### G12.4 — Multi-tenant readiness

- Все guest-тексты, феки, FAQ, контакты — параметризованы по `business_id`.
- Reuse SaaS-фазы из `docs/saas_roadmap.md`.

---

## 4. Безопасные правила работы

Из `EasyCamp-Teplo/CLAUDE.md`:

- production-sensitive репо
- read before editing
- небольшие коммиты, явный rollback path для любого изменения, влияющего на брони
- не печатать `.env` / `google-credentials.json`
- следить за overlap-гардом и SQLite миграциями (раз уж добавляем новые статусы / таблицы)

Дополнительно для guest-flow:

- любая транзакция типа cancel/payment должна писать audit-запись
- статусы броней меняются только через `BookingService` (не raw SQLAlchemy в хендлерах)

---

## 5. Зависимости / порядок

```
G10.1 -> G10.4
G10.2 -> G10.4
G10.3 (parallel with G10.1/G10.2)

G11.1 -> G11.2 -> G11.3 (после полного G10)
G12.* можно параллелить
```

---

## 6. Журнал прогресса

- 2026-04-27: roadmap создан, G10 запущен в работу. Скилы `obsidian-memory`, `project-discovery` добавлены в `.claude/skills/` для оптимизации токенов на повторные сессии. Старые доки `docs/AI_CONTEXT.md`, `docs/roadmap.md` помечены как superseded.
- 2026-04-27: G10.1 / G10.2 / G10.3 реализованы как код:
  - `app/telegram/handlers/guest_booking.py` — новый роутер: callback `guest:book:{house_id}` (с lambda-фильтром, чтобы не пересекаться с `guest:book:guests:`/`confirm`/`cancel`/`admin_*`), F.contact-handler с filter `_is_pending_book_contact` (даёт первый шанс booking flow до login flow), admin confirm/reject, cancel-flow (`guest:cancel:start:{id}` / `guest:cancel:confirm:{id}`).
  - `app/telegram/handlers/availability.py` — кнопка «Забронировать» теперь шлёт `guest:book:{id}` для не-админа и сохраняет `booking:create:{id}` для админа.
  - `app/main.py` — `guest_booking.router` зарегистрирован ДО `guest.router`, чтобы F.contact в booking flow перехватывался первым.
  - `app/telegram/handlers/guest.py` — добавлена кнопка «🚫 Отменить бронь» в карточку `guest:my_booking`. Time-gate инструкции переведён с хардкода 24h на `guest_instruction_open_hours` (default 24).
  - `app/services/global_settings.py` — новый хелпер: `get_str/get_int/set_value`, типизированные accessor'ы `get_guest_cancel_window_days`/`get_guest_instruction_open_hours`, pure-функции `can_guest_self_cancel`/`is_instruction_open`.
  - `tests/test_guest_settings.py` — 9 unit-тестов pure-логики для pytest; standalone smoke-runner повторил их inline и прошёл 13/13.
  - `docs/guest/GUEST_V2_UAT_CHECKLIST.md` — добавлены секции 9/10/11 по новым flow.
- Дальше: G10.4 ручной UAT (выполняет владелец после deploy на FI). После UAT — G11 Robokassa.
