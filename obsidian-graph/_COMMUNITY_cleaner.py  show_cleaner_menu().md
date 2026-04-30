---
type: community
cohesion: 0.13
members: 22
---

# cleaner.py / show_cleaner_menu()

**Cohesion:** 0.13 - loosely connected
**Members:** 22 nodes

## Members
- [[cleaner.py]] - code - app\telegram\handlers\cleaner.py
- [[cleaner_menu_callback()]] - code - app\telegram\handlers\cleaner.py
- [[cleaner_tasks_sync_now()]] - code - app\telegram\handlers\cleaner.py
- [[cleaning_tasks_job.py]] - code - app\jobs\cleaning_tasks_job.py
- [[confirm_cleaning()]] - code - app\telegram\handlers\cleaner.py
- [[generate_cleaning_tasks_for_tomorrow()]] - code - app\jobs\cleaning_tasks_job.py
- [[get_all_upcoming_bookings()]] - code - app\telegram\handlers\cleaner.py
- [[get_cleaner_keyboard()]] - code - app\telegram\handlers\cleaner.py
- [[get_cleaning_schedule()]] - code - app\telegram\handlers\cleaner.py
- [[get_nearest_checkouts()]] - code - app\telegram\handlers\cleaner.py
- [[get_user_name()]] - code - app\telegram\auth\admin.py
- [[notify_cleaners_about_tasks()]] - code - app\jobs\cleaning_tasks_job.py
- [[run_cleaning_tasks_cycle()]] - code - app\jobs\cleaning_tasks_job.py
- [[show_cleaner_menu()]] - code - app\telegram\handlers\cleaner.py
- [[show_schedule()]] - code - app\telegram\handlers\cleaner.py
- [[Возвращает имя пользователя из БД]] - rationale - app\telegram\auth\admin.py
- [[Главное меню уборщицы]] - rationale - app\telegram\handlers\cleaner.py
- [[Подтверждение выхода на смену]] - rationale - app\telegram\handlers\cleaner.py
- [[Показать график уборок]] - rationale - app\telegram\handlers\cleaner.py
- [[Получает ВСЕ предстоящие подтвержденные брони]] - rationale - app\telegram\handlers\cleaner.py
- [[Получает список броней, у которых выезд в заданном диапазоне]] - rationale - app\telegram\handlers\cleaner.py
- [[Формирует строку с ближайшими выездами по домам]] - rationale - app\telegram\handlers\cleaner.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/cleaner.py_/_show_cleaner_menu()
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 2 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 1 edge to [[_COMMUNITY_str  settings.py]]
- 1 edge to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 1 edge to [[_COMMUNITY_cleaner_task_flow.py  get_all_users()]]

## Top bridge nodes
- [[show_cleaner_menu()]] - degree 8, connects to 2 communities
- [[cleaner.py]] - degree 10, connects to 1 community
- [[get_user_name()]] - degree 3, connects to 1 community
- [[Возвращает имя пользователя из БД]] - degree 3, connects to 1 community
- [[cleaner_tasks_sync_now()]] - degree 3, connects to 1 community