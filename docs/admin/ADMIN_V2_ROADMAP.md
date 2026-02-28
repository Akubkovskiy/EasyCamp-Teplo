# ADMIN V2 Roadmap (Teplo)

Статус: draft -> in progress
Дата: 2026-02-28

## Цель
Обновить существующую админку до современного уровня без остановки текущей работы.

## Принципы
- Zero-downtime миграция
- Переиспользование текущей бизнес-логики
- Современный UI (Next.js + shadcn)
- Ролевой доступ + audit trail
- Пошаговые релизы с rollback

## Фазы

### A) Safe Foundation
1. Инвентаризация текущей админки (`app/web/*`)
2. Карта функций: что есть/что нужно
3. Новый admin frontend scaffold (`site-stack/frontend-admin`)
4. Proxy path для новой админки (без замены старой)

### B) API modernization
1. Unified admin API for:
   - booking requests
   - bookings
   - houses
   - payments/checks
2. Стандартизация DTO/валидации
3. Audit log таблица

### C) UX/UI
1. Dashboard KPI
2. Таблица заявок с фильтрами
3. Статусы (канбан/inline actions)
4. Детальная карточка брони
5. Mobile-friendly layout

### D) Security/Quality
1. Role-based access
2. Rate limit + basic WAF headers
3. Playwright E2E
4. Lighthouse + visual regression

### E) Cutover
1. Теневой запуск (beta URL)
2. UAT
3. Переключение default admin
4. Депрекейт старых экранов

## Definition of Done
- Новая админка покрывает текущие ключевые операции
- Старый поток не сломан
- Есть тесты и rollback plan
- Подготовлен deprecation-план legacy web-admin
