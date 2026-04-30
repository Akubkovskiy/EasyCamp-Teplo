---
type: community
cohesion: 0.11
members: 27
---

# AvitoAPIService / .ensure_token()

**Cohesion:** 0.11 - loosely connected
**Members:** 27 nodes

## Members
- [[.__init__()]] - code - app\services\avito_api_service.py
- [[.block_dates()]] - code - app\services\avito_api_service.py
- [[.ensure_token()]] - code - app\services\avito_api_service.py
- [[.get_access_token()]] - code - app\services\avito_api_service.py
- [[.get_all_bookings()]] - code - app\services\avito_api_service.py
- [[.get_bookings()]] - code - app\services\avito_api_service.py
- [[.get_bookings_for_period()]] - code - app\services\avito_api_service.py
- [[.get_price_calendar()]] - code - app\services\avito_api_service.py
- [[.unblock_dates()]] - code - app\services\avito_api_service.py
- [[.update_calendar_from_local()]] - code - app\services\avito_api_service.py
- [[.update_calendar_intervals()]] - code - app\services\avito_api_service.py
- [[.update_prices()]] - code - app\services\avito_api_service.py
- [[AvitoAPIService]] - code - app\services\avito_api_service.py
- [[avito_api_service.py]] - code - app\services\avito_api_service.py
- [[Блокировка дат в календаре Avito          Args             item_id ID объяв]] - rationale - app\services\avito_api_service.py
- [[Обновить интервалы доступности в Avito на основе локальных броней          Arg]] - rationale - app\services\avito_api_service.py
- [[Обновить интервалы доступности для дома          Получает все текущие брони и]] - rationale - app\services\avito_api_service.py
- [[Обновить цены на Avito через Price Calendar API.          Args             i]] - rationale - app\services\avito_api_service.py
- [[Получение access token через client_credentials]] - rationale - app\services\avito_api_service.py
- [[Получение броней для всех объявлений          Args             item_ids Спи]] - rationale - app\services\avito_api_service.py
- [[Получение броней за период (от сегодня вперед)          Args             ite]] - rationale - app\services\avito_api_service.py
- [[Получение списка броней по объявлению          Args             item_id ID]] - rationale - app\services\avito_api_service.py
- [[Получить текущий прайс-календарь с Avito.          Args             item_id]] - rationale - app\services\avito_api_service.py
- [[Проверка и обновление токена при необходимости]] - rationale - app\services\avito_api_service.py
- [[Разблокировка дат в календаре Avito через обновление интервалов доступности]] - rationale - app\services\avito_api_service.py
- [[Сервис для работы с Avito API]] - rationale - app\services\avito_api_service.py
- [[Сервис для работы с Avito API краткосрочной аренды]] - rationale - app\services\avito_api_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/AvitoAPIService_/_.ensure_token()
SORT file.name ASC
```

## Connections to other communities
- 14 edges to [[_COMMUNITY_BookingStatus  Booking]]

## Top bridge nodes
- [[AvitoAPIService]] - degree 15, connects to 1 community
- [[Сервис для работы с Avito API]] - degree 2, connects to 1 community
- [[Получение броней за период (от сегодня вперед)          Args             ite]] - degree 2, connects to 1 community
- [[Получение броней для всех объявлений          Args             item_ids Спи]] - degree 2, connects to 1 community
- [[Сервис для работы с Avito API краткосрочной аренды]] - degree 2, connects to 1 community