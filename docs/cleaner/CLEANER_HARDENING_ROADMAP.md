# Cleaner Hardening Roadmap (Phase C10)

Статус: **ACTIVE**Дата: 2026-04-27 Автор: claude-code Основа: `docs/cleaner/VIBECODE_ROADMAP_CLEANER.md` (этапы 1..10 в коде) Цель: довести cleaner-роль до прод-готового состояния — закрыть критбаг, docked гэпы из исходного roadmap (SupplyAlert, cancel-propagation, SLA), улучшить UX подачи чека и накрыть тестами.

---

## 0. Контекст

### Что уже сделано

- Модели: `CleaningTask`, `CleaningTaskCheck`, `CleaningTaskMedia`, `SupplyAlert`, `SupplyExpenseClaim`, `CleaningRate`, `CleaningPaymentLedger`.
- Сервис `CleaningTaskService` со state-machine, чеклистом, фото, completion gate (3 фото + required checks), auto-accrue cleaning_fee по тарифу домика.
- Хендлеры:
  - `cleaner.py` — главное меню, расписания today/tomorrow/week/all.
  - `cleaner_task_flow.py` — карточка задачи, accept/decline/start/done, чеклист, прикрепление фото по подписи `#taskN`.
  - `cleaner_expenses.py` — подача чека по подписи `claim task=N amount=X items=...`, admin approve/reject -&gt; ledger, `/cleaner_payout YYYY-MM` отчёт.
  - `cleaner_admin.py` — `/cleaner_tasks_overdue`, `/cleaner_task_assign`, `/cleaner_task_close`, `/cleaner_claims_open`, `/cleaner_payout_details`, `/cleaner_payout_mark_paid`.
- Job'ы: `cleaning_tasks_job` (idempotent generation + round-robin assign + notify), `cleaning_sla_monitor` (pending overdue -&gt; escalated + alert).
- Тесты: `test_cleaning_completion_gate` (gate), `test_cleaning_task_service`(transition graph).

### Гэпы (концентрированно)

1. **CRITICAL**: `assigned_to_user_id` иногда заполняется `telegram_id`вместо `users.id`. Та же ошибка в `SupplyExpenseClaim.cleaner_user_id`. FK ссылается в неверный домен идентификаторов — поломанный payout и неправильные join'ы.
2. `SupplyAlert` нигде не создаётся: чек `need_purchase` всего лишь галочка, админ ничего не получает.
3. Cancel брони (включая новый G10.2 self-service) не отменяет связанную `CleaningTask` — остаётся в `pending`.
4. SLA-monitor покрывает только `pending -> escalated`. Случаи `accepted` слишком долго без `in_progress` и `in_progress` после force-done deadline не обработаны.
5. Подача чека идёт через regex caption — UX плохой, ошибки пользователя теряются молча.
6. Decline-flow не предлагает причины (preset). Пишется хардкод `declined_in_ui`.
7. Тесты: нет покрытия accrual, expense-claim ledger, idempotent task creation, cancel propagation.

---

## 1. Phase C10 — Hardening (план на сегодня)

### C10.0 — CRIT: telegram_id vs [users.id](http://users.id)

- \[ \] `cleaner_task_flow._do_transition` передаёт `cleaner_user_id=callback.from_user.id` (telegram_id) в `transition_status`. Заменить на резолвинг `User.id` по `telegram_id` через DB.
- \[ \] `cleaner_expenses.cleaner_claim_submit` пишет `SupplyExpenseClaim.cleaner_user_id = message.from_user.id` (telegram_id). Зарезолвить в `User.id` или отказать, если пользователь не зарегистрирован как cleaner.
- \[ \] Миграция данных не нужна, если флоу принять/начать/закончить ещё не использовался в проде с не-pre-assigned задачами. Проверить: `SELECT id, assigned_to_user_id FROM cleaning_tasks WHERE assigned_to_user_id IS NOT NULL` — все ли значения совпадают с `users.id`. Если есть «телеграмные» — заменить точечно скриптом перед deploy.
- \[ \] Тест: `_do_transition` пишет в `assigned_to_user_id` именно `User.id`, не `telegram_id`.

### C10.1 — Supply alert wiring

- \[ \] При toggle `need_purchase = True` — создавать `SupplyAlert(status=NEW, items_json=...)` (если на ту же задачу уже есть `NEW`/`IN_PROGRESS` — обновить, не дублить).
- \[ \] Опционально: после toggle спрашивать кратко «что именно докупить?» через follow-up message (3-4 кнопки с типовыми позициями + custom) и записывать в `items_json`.
- \[ \] Уведомлять админов о новом `SupplyAlert` (обычная админ-нотификация с inline кнопкой «Resolve»).
- \[ \] Toggle `need_purchase = False` — переводить активный alert в `RESOLVED`.
- \[ \] Тест: тогл создаёт ровно 1 alert, повторный тогл TRUE→TRUE не дублирует.

### C10.2 — Booking cancel → task cancel

- \[ \] Хук в `BookingService.cancel_booking`: после установки `BookingStatus.CANCELLED` найти связанную `CleaningTask` и перевести в `CleaningTaskStatus.CANCELLED` (если не terminal).
- \[ \] Если на задачу уже начислен `cleaning_fee` (status в ledger ≠ CANCELLED) — пометить ledger-запись `CANCELLED` с комментарием «booking cancelled».
- \[ \] Уведомить уборщицу, если ей задача уже была назначена.
- \[ \] Тест: cancel booking → task=CANCELLED, ledger=CANCELLED, без падений.

### C10.3 — SLA monitor расширение

- \[ \] Параметры в `Settings`/`GlobalSetting`:
  - `cleaning_start_window_min` (default 120) — за сколько минут после `accepted` ожидаем `in_progress`.
  - `cleaning_force_done_deadline_min` (default null) — крайний срок завершения от `started_at`.
- \[ \] Job отдельно проверяет «accepted и долго не in_progress» и «in_progress и долго не done», шлёт админу алерт. Не переводит статус — только уведомляет.
- \[ \] Anti-spam: на каждой задаче храним `last_alert_at` per rule (новое поле `notes`-JSON или отдельная мини-таблица; для MVP — `notes` строкой с тегами `[alert_start_overdue=ts]`).
- \[ \] Тест: monitor шлёт по 1 алерту, повторный прогон без новых триггеров — silent.

### C10.4 — FSM для подачи чека расходников

- \[ \] Заменить regex-caption поток на FSM:
  1. `cleaner:expense:new` → выбор задачи (список последних 3-5 «active»).
  2. Выбор позиций (мульти-выбор inline-кнопок: моющее / губки / тряпки / пакеты / прочее → текст).
  3. Сумма (number-only message).
  4. Фото чека (next message).
  5. Подтверждение → создаётся `SupplyExpenseClaim(status=SUBMITTED)`.
- \[ \] Старый regex-handler оставить как fallback на 1 релиз, дальше убрать.
- \[ \] Тест: FSM-переходы (можно как unit на pure-helper'ы валидации суммы и позиций).

### C10.5 — Decline reasons

- \[ \] При нажатии «❌ Отказаться» — показать 3-4 preset-кнопки причин («Болею», «Занята», «Слишком далеко», «Другое»). При «Другое» — попросить текст.
- \[ \] Сохранять в `task.decline_reason`.
- \[ \] Алерт админу с причиной.

### C10.6 — Tests + UAT

- \[ \] `test_cleaning_accrual.py`: при DONE создаётся ровно 1 `cleaning_fee` ledger-запись с amount = active rate, и при повторном вызове DONE дубль не появляется.
- \[ \] `test_supply_alert.py`: тогл `need_purchase` создаёт `SupplyAlert(NEW)` идемпотентно; tогл False → RESOLVED.
- \[ \] `test_booking_cancel_propagation.py`: cancel booking → task=CANCELLED, ledger entry CANCELLED.
- \[ \] UAT-чеклист (ниже).

---

## 2. Phase C11 — UX и расширения (после C10)

- C11.1: чеклист с группировкой по блокам A-F (как в исходном roadmap), если владелец захочет более детальный — пока flat-список рабочий.
- C11.2: фото с автоприкреплением без `#taskN` в подписи, если уборщица активно ведёт ровно одну задачу.
- C11.3: web-админ страница для cleaning_tasks (фильтры/поиск/ drill-down).
- C11.4: автогенерация задач не только за день вперёд, но и для same-day выездов (если бронь подтверждена утром на сегодняшний выезд).

## 3. Безопасность работы

Из `EasyCamp-Teplo/CLAUDE.md`:

- production-sensitive репо.
- read before editing, маленькие коммиты, явный rollback.
- никаких секретов.
- любое изменение, влияющее на ledger (выплаты), сначала юнит-тестим и только потом деплоим.

## 4. UAT-чеклист (для ручного прогона после deploy)

- \[ \] CRIT: создать новую `CleaningTask` без pre-assignment, уборщица принимает → проверить что `assigned_to_user_id == users.id` (не telegram).
- \[ \] CRIT: cleaner подаёт чек → проверить `SupplyExpenseClaim.cleaner_user_id == users.id`.
- \[ \] CRIT: при approve чека `CleaningPaymentLedger.cleaner_user_id == users.id`.
- \[ \] Toggle `need_purchase = True` → админ получил уведомление о `SupplyAlert`, в БД ровно 1 NEW alert.
- \[ \] Cancel guest booking → связанная task становится CANCELLED.
- \[ \] Cleaner не успел нажать «Принять» в окне (`cleaning_confirm_window_min`) → SLA-monitor шлёт алерт и переводит в ESCALATED.
- \[ \] Cleaner принял, но не нажимает «Начать» 2+ часа → SLA-monitor шлёт алерт без смены статуса.
- \[ \] Подача чека через FSM проходит за 4 шага (задача / позиции / сумма / фото) и создаёт claim в SUBMITTED.
- \[ \] Decline с preset-кнопкой «Болею» → `task.decline_reason='ill'` (или как договоримся), админ получил уведомление с причиной.
- \[ \] Тесты в Docker: `pytest tests/test_cleaning_*.py` — все зелёные.

## 5. Журнал прогресса

- 2026-04-27: roadmap создан.
- 2026-04-27: реализованы C10.0, C10.1, C10.2, C10.6:
  - **C10.0**: добавлен `resolve_user_db_id` в `app/telegram/auth/admin.py`. `cleaner_task_flow._do_transition` и `cleaner_receive_photo` теперь резолвят `telegram_id -> users.id` перед записью в FK. `cleaner_expenses.cleaner_claim_submit` отказывает в подаче чека, если cleaner не зарегистрирован в БД (вместо записи telegram_id в `users.id` FK).
  - **C10.1**: новые методы `CleaningTaskService.open_supply_alert` (idempotent) и `resolve_supply_alerts`. В `cleaner_toggle_check` хук: `need_purchase=True` создаёт `SupplyAlert(NEW)` и шлёт админам уведомление; `need_purchase=False` помечает активные alerts `RESOLVED`.
  - **C10.2**: `BookingService.cancel_booking` теперь каскадно вызывает `_cascade_cancel_cleaning`: перевод task в CANCELLED (если не terminal), `cleaning_fee` ledger-записи помечаются CANCELLED, уборщице уходит best-effort нотификация (через `_notify_cleaner_about_cancel`).
  - **C10.6**: `tests/test_cleaner_hardening.py` — 4 теста: accrual idempotency, supply alert open+resolve, cancel propagation на DONE-задачу (только ledger), cancel propagation на активную задачу (task+ledger). Покрытие FK-резолва и каскада.
- Открыто на следующий заход: C10.3 (SLA monitor extension), C10.4 (FSM expense-claim вместо regex caption), C10.5 (decline reasons preset).
