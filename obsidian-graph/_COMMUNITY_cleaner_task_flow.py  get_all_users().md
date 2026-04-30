---
type: community
cohesion: 0.06
members: 44
---

# cleaner_task_flow.py / get_all_users()

**Cohesion:** 0.06 - loosely connected
**Members:** 44 nodes

## Members
- [[UserAddStates]] - code - app\telegram\handlers\settings_users.py
- [[_do_transition()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[_get_tasks()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[_is_task_photo()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[_notify_admins()]] - code - app\api\site_leads.py
- [[_notify_admins_supply_alert()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[_resolve_house_id()]] - code - app\api\site_leads.py
- [[_task_actions_keyboard()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_claim_submit()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[cleaner_receive_photo()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_accept()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_checks()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_decline()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_done()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_flow.py]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_photo_hint()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_start()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_task_view()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_tasks_list()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[cleaner_toggle_check()]] - code - app\telegram\handlers\cleaner_task_flow.py
- [[create_site_lead()]] - code - app\api\site_leads.py
- [[decline_cleaning()]] - code - app\telegram\handlers\cleaner.py
- [[get_all_users()]] - code - app\telegram\auth\admin.py
- [[get_async_session()]] - code - app\api\site_leads.py
- [[guest_feedback_message()]] - code - app\telegram\handlers\guest.py
- [[process_user_id()]] - code - app\telegram\handlers\settings_users.py
- [[process_user_name()]] - code - app\telegram\handlers\settings_users.py
- [[remove_user_handler()]] - code - app\telegram\handlers\settings_users.py
- [[require_site_token()]] - code - app\api\site_leads.py
- [[resolve_user_db_id()]] - code - app\telegram\auth\admin.py
- [[settings_users.py]] - code - app\telegram\handlers\settings_users.py
- [[settings_users_menu()]] - code - app\telegram\handlers\settings_users.py
- [[show_users_list()]] - code - app\telegram\handlers\settings_users.py
- [[site_leads.py]] - code - app\api\site_leads.py
- [[start_add_user()]] - code - app\telegram\handlers\settings_users.py
- [[validate_dates()]] - code - app\api\site_leads.py
- [[Возвращает PK `users.id` по `telegram_id`. Используется для записи     в FK-кол]] - rationale - app\telegram\auth\admin.py
- [[Возвращает всех пользователей из БД]] - rationale - app\telegram\auth\admin.py
- [[Меню управления пользователями]] - rationale - app\telegram\handlers\settings_users.py
- [[Начало добавления пользователя]] - rationale - app\telegram\handlers\settings_users.py
- [[Обработка ID пользователя]] - rationale - app\telegram\handlers\settings_users.py
- [[Обработка имени и сохранение]] - rationale - app\telegram\handlers\settings_users.py
- [[Показать список пользователей определенной роли]] - rationale - app\telegram\handlers\settings_users.py
- [[Удаление пользователя]] - rationale - app\telegram\handlers\settings_users.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/cleaner_task_flow.py_/_get_all_users()
SORT file.name ASC
```

## Connections to other communities
- 21 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 6 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 2 edges to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 1 edge to [[_COMMUNITY_GlobalSetting  global_settings.py]]
- 1 edge to [[_COMMUNITY_cleaner.py  show_cleaner_menu()]]
- 1 edge to [[_COMMUNITY_houses.py  HouseUpdate]]

## Top bridge nodes
- [[get_all_users()]] - degree 11, connects to 3 communities
- [[cleaner_claim_submit()]] - degree 4, connects to 2 communities
- [[UserAddStates]] - degree 3, connects to 2 communities
- [[site_leads.py]] - degree 9, connects to 1 community
- [[resolve_user_db_id()]] - degree 6, connects to 1 community