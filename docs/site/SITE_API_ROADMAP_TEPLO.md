# Roadmap: сайт-визитка + бронирование + API (Teplo)

Дата: 2026-02-28
Статус: Draft v1 (до старта кодинга)

---

## 1) Цель
Собрать современный продуктовый контур:
1. **Публичный сайт-визитка** (SEO + контент + лид-формы)
2. **Онлайн-бронирование** (даты/домики/заявка/оплата)
3. **API слой** (для Telegram-бота, веба, интеграций)

Сразу проектируем под масштабирование на другие базы (multi-tenant подход).

---

## 2) Что критично не сломать (инфра-факт)

На сервере сейчас уже работает VPN-стек vpnbot и занимает фронтовые порты:
- 80/tcp, 443/tcp+udp обслуживаются docker-контейнерами vpnbot (`nginx-*`, `upstream-*`)
- wildcard-домен в текущем конфиге: `*.teplo-v-arkhyze.ru` + `teplo-v-arkhyze.ru`
- важный активный конфиг:
  - `/root/vpnbot/config/nginx.conf`
  - `/root/vpnbot/config/upstream.conf`
  - `/root/vpnbot/config/override.conf`
- в `ARCHITECTURE.txt` явно указано: **не трогать `location.conf`**, особенно `location /` (сломает маршрутизацию VPN)

### Вывод
Новый сайт нельзя «ставить поверх» 80/443 напрямую и нельзя менять базовые VPN location-блоки.

---

## 3) Безопасная схема деплоя (рекомендовано)

### Вариант A (предпочтительный)
- Запускаем сайт+api отдельным docker-compose проектом на внутренних портах (например 3000/8080)
- Публикуем наружу через **отдельный subdomain** в `/root/vpnbot/config/override.conf`, например:
  - `site.teplo-v-arkhyze.ru` -> frontend
  - `api.teplo-v-arkhyze.ru` -> backend
- Используем отдельные cert-файлы (по аналогии с `claw.teplo-v-arkhyze.ru`)

### Вариант B (если нужен один домен)
- `teplo-v-arkhyze.ru` -> frontend
- `teplo-v-arkhyze.ru/api/*` -> backend
- Но только отдельным `server`-блоком в `override.conf` без изменения базовых VPN-путей.

---

## 4) Современный стек (предложение)

## Frontend
- **Next.js 14/15 (App Router)**
- **TypeScript**
- **Tailwind CSS v4 + shadcn/ui**
- Server Components + ISR/SSR для SEO и скорости

## Backend/API
- **FastAPI** (Python)
- **PostgreSQL**
- **SQLAlchemy + Alembic**
- **Pydantic v2**
- OpenAPI/Swagger out-of-box

## Infra
- Docker Compose
- Reverse proxy через уже существующий vpnbot nginx override
- S3-compatible storage (опционально для галереи)

---

## 5) Skills, которые нужны для реализации

Планируемые навыки (через ClawHub):
- frontend:
  - `nextjs-expert`
  - `tailwind-v4-shadcn`
- backend/api:
  - `fastapi`
  - `api-dev`
  - `pg`
- infra:
  - `docker-compose`
  - `nginx`

Примечание: при первой попытке установки был rate-limit у ClawHub. Нужен повтор через паузу/повторный запуск.

---

## 6) Архитектура приложения (MVP -> Product)

## Модули MVP
1. Landing
2. Каталог домиков
3. Проверка дат / форма брони
4. Контакты / как добраться / FAQ
5. API для бронирования
6. Админ-минимум (просмотр заявок)

## Модули Product v2
1. Личный кабинет гостя на вебе
2. Онлайн-оплата с вебхуками
3. Партнёры (каталог + лиды)
4. Мультиобъектность (несколько баз)

---

## 7) Этапы реализации (подход «маленькие шаги + коммиты»)

## E0 — Infra Baseline (безопасность)
- Снять snapshot текущих конфигов vpnbot
- Подготовить отдельный compose для site/api
- Проверить, что VPN-трафик не деградирует

## E1 — Front scaffold
- Next.js + Tailwind + базовый layout
- Страницы: Home, Houses, Contacts, FAQ

## E2 — API scaffold
- FastAPI проект + health + OpenAPI
- DB + миграции + базовые модели House/BookingRequest

## E3 — Booking flow MVP
- На фронте форма проверки дат и заявки
- В API создание booking request
- Нотификация в Telegram админа

## E4 — Routing on domain
- Subdomain proxy в vpnbot `override.conf`
- smoke-тесты доступности и TLS

## E5 — Admin MVP
- Просмотр заявок, смена статуса
- Логи и базовые метрики

## E6 — Hardening
- rate limiting, input validation, audit log
- backup DB + restore test

## E7 — UAT + launch
- UAT чеклист
- релиз и пост-релиз мониторинг

---

## 8) Критические ограничения / правила изменения прода

1. Не менять `location.conf`.
2. Не удалять/ломать существующие server blocks VPN.
3. Любые правки reverse proxy — только через отдельный server_name в `override.conf`.
4. Перед reload nginx: `nginx -t` внутри контейнера.
5. Деплой только через staged-коммиты и smoke после каждого этапа.

---

## 9) Что нужно от владельца перед стартом кодинга

1. Подтвердить боевые субдомены:
   - `site.teplo-v-arkhyze.ru`
   - `api.teplo-v-arkhyze.ru`
2. Подтвердить основной язык сайта (RU-only или RU+EN).
3. Дать контент-ядро:
   - тексты оффера
   - фото домиков
   - цены/правила/FAQ
4. Подтвердить оплату (интегратор/провайдер).

---

## 10) Definition of Done (MVP)

- Публичный сайт доступен по subdomain и не влияет на VPN
- Работает форма бронирования end-to-end
- API документирован и покрыт smoke-тестами
- Админ получает заявки и может менять статус
- Есть rollback-инструкция и резервные копии
