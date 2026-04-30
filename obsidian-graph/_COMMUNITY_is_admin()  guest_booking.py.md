---
type: community
cohesion: 0.09
members: 34
---

# is_admin() / guest_booking.py

**Cohesion:** 0.09 - loosely connected
**Members:** 34 nodes

## Members
- [[_ask_guests_count()]] - code - app\telegram\handlers\guest_booking.py
- [[_build_guests_count_kb()]] - code - app\telegram\handlers\guest_booking.py
- [[_guest_cancel_admin_link_kb()]] - code - app\telegram\handlers\guest_booking.py
- [[_is_book_house_callback()]] - code - app\telegram\handlers\guest_booking.py
- [[_is_cleaner_claim_photo()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[_is_pending_book_contact()]] - code - app\telegram\handlers\guest_booking.py
- [[_review_claim()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[_send_admin_booking_notification()]] - code - app\telegram\handlers\guest_booking.py
- [[_user_contact_from_db()]] - code - app\telegram\handlers\guest_booking.py
- [[approve_claim()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[cleaner_admin.py]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_claims_open()]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_expense_hint()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[cleaner_expenses.py]] - code - app\telegram\handlers\cleaner_expenses.py
- [[cleaner_payout_details()]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_payout_mark_paid()]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_payout_report()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[cleaner_task_assign()]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_task_close()]] - code - app\telegram\handlers\cleaner_admin.py
- [[cleaner_tasks_overdue()]] - code - app\telegram\handlers\cleaner_admin.py
- [[get_env_admins()]] - code - app\telegram\auth\admin.py
- [[guest_book_admin_confirm()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_book_admin_reject()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_book_cancel()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_book_confirm()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_book_guests_count()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_book_start()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_booking.py]] - code - app\telegram\handlers\guest_booking.py
- [[guest_cancel_start()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_pay_reject()]] - code - app\telegram\handlers\guest.py
- [[is_admin()]] - code - app\telegram\auth\admin.py
- [[reject_claim()]] - code - app\telegram\handlers\cleaner_expenses.py
- [[Получает админов из переменных окружения]] - rationale - app\telegram\auth\admin.py
- [[Проверяет, является ли пользователь админом (env + db)]] - rationale - app\telegram\auth\admin.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/is_admin()_/_guest_booking.py
SORT file.name ASC
```

## Connections to other communities
- 19 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 9 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 4 edges to [[_COMMUNITY_GlobalSetting  global_settings.py]]
- 3 edges to [[_COMMUNITY_create.py  build_month_keyboard()]]
- 2 edges to [[_COMMUNITY_str  settings.py]]
- 2 edges to [[_COMMUNITY_cleaner_task_flow.py  get_all_users()]]
- 1 edge to [[_COMMUNITY_cleaner.py  show_cleaner_menu()]]
- 1 edge to [[_COMMUNITY_on_startup()  AutoSyncMiddleware]]

## Top bridge nodes
- [[is_admin()]] - degree 23, connects to 5 communities
- [[guest_booking.py]] - degree 17, connects to 3 communities
- [[guest_cancel_start()]] - degree 6, connects to 3 communities
- [[guest_book_start()]] - degree 6, connects to 2 communities
- [[_ask_guests_count()]] - degree 5, connects to 2 communities