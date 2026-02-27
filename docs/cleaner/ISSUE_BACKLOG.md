# Cleaner v2 — Issue Backlog (для старта реализации)

## EPIC-1: Schema foundation

### ISSUE-1: Добавить таблицы cleaner domain
**Scope:** `cleaning_tasks`, `cleaning_task_checks`, `cleaning_task_media`, `supply_alerts`  
**Acceptance Criteria:**
- Миграция выполняется на пустой и существующей БД
- Таблицы и индексы созданы
- `booking_id` в `cleaning_tasks` уникален

### ISSUE-2: Добавить таблицы финансов
**Scope:** `cleaning_rates`, `cleaning_payments_ledger`, `supply_expense_claims`  
**Acceptance Criteria:**
- Поддерживается тариф по дому
- Есть ledger для начислений/компенсаций
- Нет дубля `cleaning_fee` по одной задаче

## EPIC-2: Service layer

### ISSUE-3: CleaningTaskService + статусные переходы
**Acceptance Criteria:**
- Валидные переходы работают
- Невалидные переходы отклоняются
- Есть unit test на переходы

### ISSUE-4: Автоначисление уборки при done
**Acceptance Criteria:**
- При `DONE` создаётся `cleaning_fee`
- Берётся активный тариф домика
- Повторно начисление не создаётся

## EPIC-3: Telegram cleaner UX

### ISSUE-5: Карточка задачи + кнопки действия
**Acceptance Criteria:**
- pending: принять/отказаться
- accepted: начать
- in_progress: чеклист/фото/завершить

### ISSUE-6: Чеклист и media gate
**Acceptance Criteria:**
- Без обязательных чеков + 3 фото `done` невозможен
- Статус и прогресс видны в UI

## EPIC-4: Expense claims

### ISSUE-7: Подача чека уборщицей
**Acceptance Criteria:**
- Фото + сумма + позиции сохраняются как claim
- claim получает `submitted`

### ISSUE-8: Модерация claim админом
**Acceptance Criteria:**
- approve/reject через Telegram
- approve создаёт `supply_reimbursement` в ledger

## EPIC-5: SLA + Admin

### ISSUE-9: SLA монитор
**Acceptance Criteria:**
- pending timeout => escalated
- антиспам алертов работает

### ISSUE-10: Отчёт «к выплате»
**Acceptance Criteria:**
- Показывает уборку + компенсации отдельно
- Детализация: дата, дата уборки, домик, тип, сумма, чек

---

## План коммитов (регулярные)
1. `feat(cleaner): add schema + migration`
2. `feat(cleaner): add service transitions + accrual`
3. `feat(cleaner): add telegram task flow`
4. `feat(cleaner): add checklist and media gate`
5. `feat(cleaner): add expense claim submit/review`
6. `feat(cleaner): add payout report and SLA monitor`
7. `test(cleaner): add unit/integration coverage`
