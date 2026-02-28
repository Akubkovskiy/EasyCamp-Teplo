# EasyCamp-Teplo — индекс контекста (для Obsidian)

Дата: 2026-02-27
Источник: текущий код/доки репозитория `/root/easycamp-bot`

## 1) Что это за проект

EasyCamp-Teplo — B2B SaaS/MVP для базы отдыха (пилот: «Тепло», Архыз):
- FastAPI backend
- Telegram-бот (aiogram 3.x) для операционки
- Web-admin (шахматка/CRUD/настройки/онбординг)
- Интеграции: Avito API + webhook, Google Sheets sync
- SQLite + SQLAlchemy + Alembic
- APScheduler для фоновых задач

---

## 2) Архитектурная карта (по коду)

### Точка входа
- `app/main.py`
  - Поднимает FastAPI
  - Подключает rate limiting (`slowapi`) и request logging middleware
  - Регистрирует API, Avito и web-роутеры
  - На startup:
    - Smart Recovery из backup (`backup_service.restore_latest_backup`)
    - `init_db()`
    - старт scheduler
    - optional auto-sync middleware для Telegram
    - initial background sync в Google Sheets
    - refresh user cache
    - запуск Telegram polling в фоне

### Ключевые каталоги
- `app/api` — health-check
- `app/avito` — webhook, oauth, схемы Avito
- `app/core` — config, logging, security, rate limiter, тексты
- `app/services` — бизнес-логика (booking/house/sync/settings/backup/...)
- `app/jobs` — фоновые задачи
- `app/telegram` — бот, handlers, menu, UI, middlewares, auth
- `app/web` — веб-админка (routers/templates/deps/middleware)

---

## 3) Доменная модель (БД)

## Основные сущности (`app/models.py`)

### House
- `id`, `name`, `description`, `capacity`
- Динамический контент: `wifi_info`, `address_coords`, `checkin_instruction`, `rules_text`
- Промо: `promo_description`, `promo_image_id`, `guide_image_id`

### Booking
- Связь с домом: `house_id`
- Гость: `guest_name`, `guest_phone`
- Даты: `check_in`, `check_out`
- Финансы: `total_price`, `advance_amount`, `commission`, `prepayment_owner`
- Статус: `new|confirmed|paid|checking_in|checked_in|cancelled|completed`
- Источник: `avito|telegram|direct|other`
- `external_id` для Avito

### User
- `telegram_id` (опционален для web-only admin), `username`, `hashed_password`
- `role`: `owner|admin|cleaner|guest`
- `name`, `phone`

### GlobalSetting
- key-value хранилище глобальных параметров

### Миграции Alembic
- `2f8620082508_baseline.py`
- `545e7fe519d5_add_auth_fields_to_user.py`
- `f93d2f12f708_fix_schema_discrepancies.py`

---

## 4) Интеграции и потоки данных

## Avito
- Вход:
  - `POST /webhook` (`app/avito/webhook.py`)
  - OAuth роуты в `app/avito/oauth.py`
- Логика:
  - маппинг статусов Avito → внутренние статусы
  - upsert брони через `BookingService.create_or_update_avito_booking`
  - привязка `item_id -> house_id` через `AVITO_ITEM_IDS` в env

## Google Sheets
- `app/services/sheets_service.py`
- Лист `Все брони` + `Dashboard`
- Русификация статусов/источников, форматирование, сортировка
- Sync throttling:
  - `_sync_cache_ttl_seconds`
  - `_is_syncing`
  - `sync_if_needed(force=...)`

## Telegram
- Polling в фоне из FastAPI startup
- Основные группы handler’ов:
  - админ-меню, брони, доступность, дома, контакты, синк, настройки, cleaner, guest

## Web Admin
- Роутеры:
  - `auth_web`, `admin_web`, `setup_web`, `settings_web`, `house_web`, `booking_web`
- Статика: `/admin-web/static`
- Темплейты: dashboard/login/settings/setup

---

## 5) Карта HTTP-роутов (срез)

### API/служебные
- `GET /health`
- `POST /webhook` (Avito)
- `GET /auth`, `GET /callback` (Avito OAuth)

### Web-admin
- Auth: `GET/POST /login`, `GET /logout`
- Dashboard: `GET /`
- Setup Wizard: `GET/POST /`, `/step1`, `/step2`, `/step3`
- Houses: `GET/POST /`, `GET /new`, `GET/POST /{house_id}`, `POST /{house_id}/delete`
- Bookings: `GET /new`, `GET /{booking_id}`, `POST /new`, `POST /{booking_id}`
- Settings: `GET/POST /`

---

## 6) Бизнес-логика бронирований (важное)

`app/services/booking_service.py`

- Проверка конфликтов дат: `check_availability`
- Создание брони:
  - валидация доступности
  - расчет полей предоплаты
  - опциональная блокировка дат в Avito
  - async sync в Sheets
- Отмена/удаление:
  - статус `cancelled` или физическое удаление
  - разблокировка дат Avito (кроме Avito-native броней)
- Обновление:
  - повторная проверка конфликтов при смене дат/домика
- Upsert из Avito webhook

---

## 7) Конфигурация (важные env-направления)

`app/core/config.py`

- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- DB: `DATABASE_URL` (авто-выбор `/app/data/easycamp.db` в контейнере)
- Sheets: `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_CREDENTIALS_FILE`
- Avito: `AVITO_CLIENT_ID`, `AVITO_CLIENT_SECRET`, `AVITO_ITEM_IDS`, `AVITO_WEBHOOK_*`
- Sync: `SYNC_ON_BOT_START`, `SYNC_ON_USER_INTERACTION`, `SYNC_CACHE_TTL_SECONDS`
- Rate limit: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_WEBHOOK`
- Branding/SaaS: `PROJECT_*`, `CONTACT_*`, `PAYMENT_*`
- Auth/Web: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `SETUP_SECRET`

---

## 8) Что нового/неочевидного (по сравнению с «обычным» ботом)

1. **Есть полноценная web-admin часть**, не только Telegram.
2. **Setup Wizard** (step1..step3) встроен в web-поток.
3. **Smart Recovery** при старте (восстановление backup).
4. **Умный sync-throttling** в Google Sheets, чтобы не упираться в лимиты.
5. **Role-модель расширена**: owner/admin/cleaner/guest + web-auth поля в User.
6. **Комбинированная эксплуатация**: webhook + polling + scheduler внутри одного процесса.

---

## 9) Риски/техдолг (коротко)

- Один процесс совмещает API + polling + jobs → риск «шумных» рестартов.
- SQLite годится для MVP, но при росте нагрузки нужен PostgreSQL.
- Часть бизнес-логики может дублироваться между Telegram/Web потоками (проверить консистентность).
- Avito mapping через строку `AVITO_ITEM_IDS` требует строгой дисциплины конфигурации.

---

## 10) Рекомендуемые next-step заметки для Obsidian

1. `EasyCamp/Architecture/Runtime-Topology.md`
2. `EasyCamp/DataModel/ERD-Booking-House-User.md`
3. `EasyCamp/Integrations/Avito-Webhook-Flow.md`
4. `EasyCamp/Integrations/GoogleSheets-Sync-Strategy.md`
5. `EasyCamp/Ops/Env-and-Secrets-Map.md`
6. `EasyCamp/Risks/MVP-Scaling-Risks.md`

---

## 11) Быстрый чек-лист погружения нового разработчика

- Прочитать: `README.md`, `docs/DEPLOYMENT.md`, `app/main.py`
- Посмотреть модели: `app/models.py`
- Пройти сервисы: `booking_service.py`, `sheets_service.py`, `avito_sync_service.py`
- Пройти web routers + templates
- Пройти Telegram handlers (особенно bookings/availability/houses/settings)
- Проверить env и локальный запуск

---

## 12) Журнал изменений (2026-02-27) — Cleaner v2

Что уже реализовано:
- Добавлены доменные сущности и миграции для cleaner-задач и финансов:
  - `cleaning_tasks`, `cleaning_task_checks`, `cleaning_task_media`, `supply_alerts`
  - `cleaning_rates`, `cleaning_payments_ledger`, `supply_expense_claims`
- Реализован `CleaningTaskService`:
  - idempotent создание задач
  - машина статусов
  - блокировка `done` без обязательного чеклиста и фото
  - автоначисление `cleaning_fee` при завершении
- Добавлен Telegram flow уборщицы:
  - список задач / карточка задачи
  - принять / отказаться / начать / завершить
  - чеклист и загрузка фото
- Добавлен flow чеков расходников:
  - уборщица отправляет чек (фото + сумма + позиции)
  - админ approve/reject
  - при approve создаётся компенсация в ledger
- Добавлены админ-команды:
  - `/cleaner_tasks_sync`
  - `/cleaner_tasks_overdue`
  - `/cleaner_task_assign`
  - `/cleaner_task_close`
  - `/cleaner_claims_open`
  - `/cleaner_payout`, `/cleaner_payout_details`, `/cleaner_payout_mark_paid`
- Добавлены job’ы:
  - генерация cleaner-задач
  - SLA-монитор эскалаций
- Прогнаны авто-проверки:
  - `pytest` (all green)
  - smoke `verify_cleaner_v2_flow.py` (green)
  - миграции `alembic upgrade head` (green)

### TODO (ручная приёмка в UI)
- [ ] Прогнать в Telegram полный сценарий роли уборщицы (happy path).
- [ ] Проверить блокировку завершения без чеклиста/фото.
- [ ] Проверить отказ от задачи и эскалацию админам.
- [ ] Проверить чек расходников: submit → approve/reject.
- [ ] Проверить отчёт выплат и отметку `paid` после подтверждения.

---

## 13) Guest v2 — контекст и план

- Добавлен отдельный roadmap: `docs/guest/VIBECODE_ROADMAP_GUEST_V2.md`
- Ключевая модель: `Витрина до авторизации -> ЛК после авторизации`
- Зафиксированы требования:
  - FAQ + обратная связь
  - `Моя бронь` (вместо `Мои брони`)
  - модуль `Партнёры` (MVP-заглушка -> каталог)
  - SaaS-ready подход: минимум хардкода, максимум конфигов

### TODO (guest, до кодинга)
- [x] Утвердить IA неавторизованного меню
- [x] Утвердить IA авторизованного кабинета
- [x] Утвердить copy кнопок и текстов
- [ ] Утвердить конфиг-схему (feature flags + контент)

### Execution tracking
- Добавлен чеклист выполнения: `docs/guest/GUEST_V2_IMPLEMENTATION_CHECKLIST.md`
- Текущий активный этап: `G1 — Витрина (unauth mode)`

### Последние правки по UX (2026-02-27, вечер)
- Неавторизованный режим: кнопка `📅 Проверить даты и забронировать`.
- Неавторизованный режим: вместо `Как добраться` использовать `📍 Где мы находимся` (атмосфера + координаты + фото).
- Авторизованный режим: отдельный детальный раздел `🛣 Как добраться` (маршрут/видео/гайд к объекту).
- В авторизованном меню приоритетные пункты: `Инструкция по заселению`, `Связаться с нами`, `Как добраться`.
- Кнопка авторизации в витрине — рабочий вариант: `🔐 Авторизоваться`.

### Прогресс реализации Guest v2 (автономно)
- G1 завершён: витрина unauth + разделённые меню unauth/auth.
- G2 завершён: усилен phone matching (normalize + last10), добавлены тесты.
- G3 завершён: обновлён auth-кабинет по новому IA.
- G4 (MVP) завершён: чек оплаты от гостя -> admin approve/reject -> обновление брони до `PAID`.
- G5 (MVP) завершён: time-gate инструкции (доступ за 24ч до заезда).
- G6 (MVP) завершён: FAQ + структурированный вопрос гостя (категория + текст) в админ-канал.
- G7 (v1) завершён: раздел партнёров переведён на конфигурируемый текстовый каталог.
- G8 (MVP) завершён: добавлены guest feature flags и условная сборка меню.
- G9 (тех) завершён: финальный прогон тестов и подготовка UAT чеклиста.

## 14) Site + API roadmap (новый трек)

- Добавлен документ: `docs/site/SITE_API_ROADMAP_TEPLO.md`
- Зафиксировано: 80/443 уже заняты VPN-стеком (`vpnbot`), правки только безопасным путём через отдельные `server_name` в `override.conf`.
- Подход: отдельные subdomain для сайта/API + отдельный compose проект.
- Прогресс: E0/E1/E2 выполнены, добавлен `site-stack` и execution-checklist `docs/site/SITE_API_EXECUTION_CHECKLIST.md`.
- В API реализованы MVP endpoints заявок на бронирование (`/houses`, `/booking-requests`).
- E3 выполнен: frontend визитка подключена к API, форма заявки отправляет бронирование end-to-end.
- Добавлен testing roadmap: `docs/site/TESTING_STACK_ROADMAP.md`.
- Установлены testing skills: `playwright-mcp`, `playwright`, `cypress`.
- Планируемый стек:
  - Front: Next.js + Tailwind v4 + shadcn/ui
  - API: FastAPI + PostgreSQL + Alembic

_Заметка подготовлена в формате Obsidian-friendly Markdown._
