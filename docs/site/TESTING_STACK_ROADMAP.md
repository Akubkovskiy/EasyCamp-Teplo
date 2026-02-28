# Testing Stack Roadmap (Site + API)

## Цель
Подключить автотесты для сайта-визитки и API до релиза.

## Треки

### T1 — API smoke/contract
- pytest + httpx
- health, houses, booking-request create/read

### T2 — UI E2E
- Playwright (приоритет)
- Cypress (резерв)
- ключевые сценарии: landing -> house -> booking form -> success

### T3 — Performance
- Lighthouse CI (mobile/desktop)
- бюджеты: LCP/CLS/INP

### T4 — Security baseline
- OWASP ZAP baseline
- проверка заголовков/простых уязвимостей

### T5 — Visual regression
- Playwright screenshot snapshots
- детект поломок верстки

## Этапы внедрения
1. Поднять smoke API тесты
2. Добавить 2 E2E сценария на UI
3. Включить Lighthouse в CI
4. Включить security baseline
5. Добавить visual regression

## Definition of Done
- API smoke зеленый
- минимум 2 E2E сценария зеленые
- Lighthouse отчёт в пределах бюджетов
- Security baseline без критических findings
