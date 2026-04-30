---
type: community
cohesion: 0.15
members: 17
---

# GoogleSheetsService / .sync_bookings_to_sheet()

**Cohesion:** 0.15 - loosely connected
**Members:** 17 nodes

## Members
- [[.__init__()_2]] - code - app\services\sheets_service.py
- [[._format_bookings_sheet()]] - code - app\services\sheets_service.py
- [[.connect()]] - code - app\services\sheets_service.py
- [[.create_dashboard()]] - code - app\services\sheets_service.py
- [[.sync_bookings_async()]] - code - app\services\sheets_service.py
- [[.sync_bookings_to_sheet()]] - code - app\services\sheets_service.py
- [[.sync_if_needed()]] - code - app\services\sheets_service.py
- [[Async wrapper для синхронизации броней]] - rationale - app\services\sheets_service.py
- [[GoogleSheetsService]] - code - app\services\sheets_service.py
- [[sheets_service.py]] - code - app\services\sheets_service.py
- [[Подключение к Google Sheets]] - rationale - app\services\sheets_service.py
- [[Сервис для работы с Google Sheets]] - rationale - app\services\sheets_service.py
- [[Сервис для синхронизации данных с Google Sheets]] - rationale - app\services\sheets_service.py
- [[Синхронизация броней в Google Sheets]] - rationale - app\services\sheets_service.py
- [[Создание Dashboard с общей статистикой]] - rationale - app\services\sheets_service.py
- [[Умная синхронизация - только если прошло достаточно времени          Args]] - rationale - app\services\sheets_service.py
- [[Форматирование листа с бронями]] - rationale - app\services\sheets_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GoogleSheetsService_/_.sync_bookings_to_sheet()
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_BookingStatus  Booking]]

## Top bridge nodes
- [[GoogleSheetsService]] - degree 10, connects to 1 community
- [[Сервис для работы с Google Sheets]] - degree 2, connects to 1 community
- [[Синхронизация броней в Google Sheets]] - degree 2, connects to 1 community
- [[Сервис для синхронизации данных с Google Sheets]] - degree 2, connects to 1 community
- [[Создание Dashboard с общей статистикой]] - degree 2, connects to 1 community