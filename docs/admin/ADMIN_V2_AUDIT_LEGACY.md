# Admin V2 — Audit Legacy Admin (`app/web/*`)

Дата: 2026-02-28

## Что найдено

### Роутеры
- `admin_web.py`
  - `GET /` (dashboard)
- `auth_web.py`
  - `GET/POST /login`, `GET /logout`
- `booking_web.py`
  - `GET /new`, `POST /new`, `GET /{booking_id}`, `POST /{booking_id}`
- `house_web.py`
  - `GET /`, `GET /new`, `POST /`, `GET/POST /{house_id}`, `POST /{house_id}/delete`
- `settings_web.py`
  - `GET/POST /`
- `setup_web.py`
  - intro + `step1..step3` (GET/POST)

### Шаблоны
- login, dashboard, settings
- houses list/form
- bookings list/create/detail
- setup intro/step1/step2/step3

## Что критично переиспользовать в Admin V2
1. Логин/сессии (`auth_web` + deps)
2. CRUD домиков (`house_web`)
3. Создание/редактирование брони (`booking_web`)
4. Настройки (`settings_web`)
5. Setup Wizard (`setup_web`) — оставить как отдельный онбординг модуль

## Gap к новой админке
- Нет современного UX (таблицы/фильтры/inline actions)
- Нет единого API-контракта под frontend
- Нет централизованного audit trail
- Нет тест-контуров UI регрессий

## Решение миграции
- Legacy web пока не трогаем (working as-is)
- Строим новый Admin V2 параллельно
- По одному модулю переключаем:
  1) Заявки/брони
  2) Домики
  3) Настройки
  4) Setup
