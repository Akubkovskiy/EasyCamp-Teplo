# UAT pending — на следующую сессию (2026-04-28)

Статус: что задеплоено сегодня и что осталось руками протестить.

---

## ✅ Уже задеплоено (FI, prod)

Цепочка cherry-pick'нутых коммитов на FI поверх FI-only avito-фиксов:

| commit | что |
|---|---|
| `096a4d1` | docs: project pack entrypoints (codex) |
| `5369165` | guest G10 self-service (booking + cancel + time-gate config) |
| `c1595d7` | cleaner C10 hardening (telegram_id→users.id, supply_alerts, cascade) |
| `6fe21b4` | site_leads `POST /api/leads` (token-protected) |
| `f52d17b` | admin-web settings: окно отмены / окно инструкции |
| `bd7fce7` | F.photo conflict fix — cleaner handlers больше не съедают фото гостя |
| `ecc3079` | env-based admin login (ADMIN_WEB_USERNAME / ADMIN_WEB_PASSWORD) |
| `657edb2` | guest pay receipt: PDF + другие document'ы |
| `e0db9ff` | UX: PAID booking → summary вместо «инструкции по оплате» |
| `0f21d44` | **G10.6 двухэтапная оплата** — задаток + остаток, % настраивается в админке |

`.env` на FI содержит `ADMIN_WEB_USERNAME=admin`, `ADMIN_WEB_PASSWORD=Teplo2026!`.
DB hotfix: 1 строка `bookings.status='cancelled'` lowercase → `CANCELLED`.

---

## ✅ Уже проверено сегодня в Telegram

- `/start` → витрина гостя (unauth) → выбор дат → выбор домика → request_contact → создание `User(role=GUEST)` + `Booking(NEW, source=TELEGRAM)`.
- Admin confirm: бронь NEW → CONFIRMED, гостю notify с кнопкой «💳 Оплата».
- Кнопка «🚫 Отменить бронь» ветка «закрытое окно» (до заезда 0 дн.): экран «Свяжитесь с админом», бронь не меняется.
- Оплата (старый одноэтапный flow): фото чека → admin approve → бронь PAID.
- **Avito-блокировка дат** при создании брони из бота — работает (даты 28-30.04 заблокировались автоматически).
- DB подтверждение цепочки статусов: NEW → CONFIRMED → PAID, advance_amount = total_price.

---

## 🟡 Pending — что протестить вручную в следующий заход

### 1. Двухэтапная оплата (G10.6) — главное

Создать **новую** бронь (бронь #57 уже PAID, не подойдёт):

1. `/start` → витрина → «📅 Проверить даты» → даты через 8+ дней (например 15.05 — 17.05) → выбрать любой свободный домик с ценой → «✅ Забронировать». Контакт уже сохранён → бот сразу спросит кол-во гостей.
2. Admin confirm в админ-чате: бронь CONFIRMED.
3. Гость → «🏠 Моя бронь» → «💳 Оплата».
   - **Ожидается:** «💰 Внесите задаток X ₽» (X = total × 30%).
   - Кнопка «📸 Отправить чек задатка».
4. Гость шлёт фото → админу прилетает 3 кнопки: «✅ Задаток (X ₽)» / «✅ Полная (+Y ₽)» / «❌ Отклонить».
5. Админ нажимает **«✅ Задаток»** → гостю «Задаток подтверждён. Остаток Y ₽ — при заселении». Бронь = CONFIRMED, advance = X.
6. Гость снова открывает «💳 Оплата» → теперь видит **«💳 Доплата при заселении: Y ₽»**, кнопка «📸 Отправить чек остатка».
7. Гость шлёт второе фото → админу опять 3 кнопки → нажимает **«✅ Полная»** → бронь = PAID, гостю «✅ Оплата подтверждена полностью».

DB-проверка: `bookings.advance_amount` дважды растёт (0 → X → total), `status` идёт CONFIRMED → CONFIRMED → PAID.

### 2. Отмена брони — ветка «отменяет сам»

На той же тестовой брони (если ещё CONFIRMED, > 7 дней до заезда):

- Гость → «🏠 Моя бронь» → «🚫 Отменить бронь».
- Должно показать «❓ Отменить бронь #N? — До заезда N дн. После отмены даты вернутся в продажу.» с кнопками «✅ Да, отменить» / «🔙 Нет, оставить».
- Confirm → status=CANCELLED, гостю «✅ Бронь #N отменена», админу уведомление, Avito-даты разблокированы.

### 3. Админ-настройки

- SSH-туннель: `ssh -L 8000:localhost:8000 fin` → `http://localhost:8000/admin-web/login`
- Логин: `admin` / `Teplo2026!` (env-based, в БД bcrypt-хэша больше не требуется).
- `/admin-web/settings` → блок «🧳 Правила для гостя» с тремя полями: окно отмены (7), окно инструкции (24), задаток % (30).
  - Изменить задаток на 50%, сохранить → следующая бронь должна посчитать задаток как 50% от total.
- `/admin-web/bookings` → должна открыться без 500 (lowercase enum hotfix).

### 4. PDF-чек

Любой бронь в стадии «надо платить» → «Отправить чек» → отправить **PDF-файл** (не фото).
- Бот: «✅ Чек отправлен администратору на проверку.»
- Админу прилетает **document** (а не photo) с теми же 3 кнопками.

### 5. Site → EasyCamp lead intake

Этот flow задеплоен на стороне EasyCamp (`POST /api/leads`), но не активирован (env `SITE_LEAD_TOKEN` пустой) и сайт teplo-v-arkhyze ещё не задеплоен с forward-кодом.

Ожидает: задеплоить `teplo-v-arkhyze` коммит `474759a`, добавить в обоих `.env` совпадающий токен, ALTER TABLE на site Postgres. См. `teplo-v-arkhyze/docs/SITE_BOOKING_ROADMAP.md` раздел «Pre-deploy».

### 6. Cleaner C10 — ещё не UAT-нили

Изменения по уборщице задеплоены (telegram_id→users.id фикс, SupplyAlert wiring, booking cancel cascade), но без живой уборщицы потестить сложно. Проверочный запрос для FI:

```sql
SELECT id, assigned_to_user_id FROM cleaning_tasks
LEFT JOIN users ON users.id = cleaning_tasks.assigned_to_user_id
WHERE cleaning_tasks.assigned_to_user_id IS NOT NULL AND users.id IS NULL;
```

Если вернёт строки — значит до C10 в БД были «телеграмные» значения в FK; нужен одноразовый data-fix.

---

## 🛠 Backlog (не блокирует UAT, но всплыло)

- **G10.5 polish:** если гость отправил **текст** в режиме ожидания чека — бот должен ответить «нужно ИМЕННО фото или PDF», а не молчать.
- **Публичный proxy `/admin-web/*`** на `teplo-v-arkhyze.ru` (сейчас доступ только через SSH-туннель). Требует override.conf в vpnbot nginx + basic-auth.
- **C10.3** SLA-monitor расширение (accepted без start, in_progress overdue).
- **C10.4** FSM expense-claim вместо regex caption.
- **С10.5** Decline reasons preset.
- **S10/S11** site forward + Alembic + retry-job.

---

## 🔁 Откат

Backup ref на FI: `deploy-pre-s10-2026-04-28` указывает на состояние ДО любого G10/C10/S10 cherry-pick. Если что-то сломается:

```bash
ssh fin
cd /root/easycamp-bot
git reset --hard deploy-pre-s10-2026-04-28
docker compose build app && docker compose up -d --force-recreate app
```

DB hotfix lowercase 'cancelled' откату не подлежит — он корректнее старого состояния.
