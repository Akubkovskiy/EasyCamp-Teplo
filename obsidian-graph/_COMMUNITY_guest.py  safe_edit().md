---
type: community
cohesion: 0.05
members: 86
---

# guest.py / safe_edit()

**Cohesion:** 0.05 - loosely connected
**Members:** 86 nodes

## Members
- [[% от total_price, который гость вносит как задаток при бронировании.     Остаток]] - rationale - app\services\global_settings.py
- [[Pure рассчитать сумму задатка от total_price по проценту.     Округление вниз д]] - rationale - app\services\global_settings.py
- [[_admin_approve_payment()]] - code - app\telegram\handlers\guest.py
- [[_is_pay_receipt_waiting()]] - code - app\telegram\handlers\guest.py
- [[_send_pay_receipt_to_admins()]] - code - app\telegram\handlers\guest.py
- [[add_user()]] - code - app\telegram\auth\admin.py
- [[admin.py]] - code - app\telegram\auth\admin.py
- [[admin.py_1]] - code - app\telegram\menus\admin.py
- [[admin_menu.py]] - code - app\telegram\handlers\admin_menu.py
- [[admin_menu_keyboard()]] - code - app\telegram\menus\admin.py
- [[back_to_admin()]] - code - app\telegram\handlers\settings.py
- [[back_to_guest_menu()]] - code - app\telegram\handlers\admin_menu.py
- [[back_to_guest_menu()_1]] - code - app\telegram\handlers\guest.py
- [[back_to_menu()]] - code - app\telegram\handlers\admin_menu.py
- [[back_to_showcase_menu()]] - code - app\telegram\handlers\guest.py
- [[build_showcase_section_rows()]] - code - app\telegram\handlers\guest.py
- [[cmd_about()]] - code - app\telegram\handlers\guest.py
- [[cmd_booking()]] - code - app\telegram\handlers\guest.py
- [[cmd_contact()]] - code - app\telegram\handlers\guest.py
- [[cmd_location()]] - code - app\telegram\handlers\guest.py
- [[cmd_login()]] - code - app\telegram\handlers\guest.py
- [[compute_advance_amount()]] - code - app\services\global_settings.py
- [[contact_admin()]] - code - app\telegram\handlers\guest.py
- [[ensure_guest_auth()]] - code - app\telegram\handlers\guest.py
- [[ensure_guest_context()]] - code - app\telegram\handlers\guest.py
- [[get_active_booking()]] - code - app\telegram\handlers\guest.py
- [[get_guest_advance_percent()]] - code - app\services\global_settings.py
- [[get_guest_context()]] - code - app\telegram\handlers\guest.py
- [[get_setting_value()]] - code - app\telegram\handlers\guest.py
- [[guest.py]] - code - app\telegram\handlers\guest.py
- [[guest.py_1]] - code - app\telegram\menus\guest.py
- [[guest_auth_prompt()]] - code - app\telegram\handlers\guest.py
- [[guest_book_contact()]] - code - app\telegram\handlers\guest_booking.py
- [[guest_directions()]] - code - app\telegram\handlers\guest.py
- [[guest_feedback_choose_category()]] - code - app\telegram\handlers\guest.py
- [[guest_feedback_start()]] - code - app\telegram\handlers\guest.py
- [[guest_house_detail()]] - code - app\telegram\handlers\guest.py
- [[guest_instruction()]] - code - app\telegram\handlers\guest.py
- [[guest_logout()]] - code - app\telegram\handlers\guest.py
- [[guest_menu_keyboard()]] - code - app\telegram\menus\guest.py
- [[guest_partners()]] - code - app\telegram\handlers\guest.py
- [[guest_pay()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_approve_advance()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_approve_full()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_approve_legacy()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_receipt_document()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_receipt_photo()]] - code - app\telegram\handlers\guest.py
- [[guest_pay_receipt_start()]] - code - app\telegram\handlers\guest.py
- [[guest_rules()]] - code - app\telegram\handlers\guest.py
- [[guest_showcase_about()]] - code - app\telegram\handlers\guest.py
- [[guest_showcase_faq()]] - code - app\telegram\handlers\guest.py
- [[guest_showcase_houses()]] - code - app\telegram\handlers\guest.py
- [[guest_showcase_location()]] - code - app\telegram\handlers\guest.py
- [[guest_showcase_menu_keyboard()]] - code - app\telegram\menus\guest.py
- [[guest_wifi()]] - code - app\telegram\handlers\guest.py
- [[handle_contact()]] - code - app\telegram\handlers\guest.py
- [[is_guest()]] - code - app\telegram\auth\admin.py
- [[is_guest_authorized()]] - code - app\telegram\handlers\guest.py
- [[main()_8]] - code - scripts\verify_guest_flow.py
- [[my_booking()]] - code - app\telegram\handlers\guest.py
- [[normalize_phone()]] - code - app\utils\phone.py
- [[phone.py]] - code - app\utils\phone.py
- [[phone_last10()]] - code - app\utils\phone.py
- [[phones_match()]] - code - app\utils\phone.py
- [[refresh_users_cache()]] - code - app\telegram\auth\admin.py
- [[remove_guest_user()]] - code - app\telegram\auth\admin.py
- [[remove_user()]] - code - app\telegram\auth\admin.py
- [[request_contact_keyboard()]] - code - app\telegram\menus\guest.py
- [[safe_edit()]] - code - app\telegram\handlers\guest.py
- [[set_guest_auth()]] - code - app\telegram\handlers\guest.py
- [[set_guest_context()]] - code - app\telegram\handlers\guest.py
- [[show_guest_menu()]] - code - app\telegram\handlers\guest.py
- [[start_handler()]] - code - app\telegram\handlers\admin_menu.py
- [[test_normalize_phone()]] - code - tests\test_phone_utils.py
- [[test_phone_utils.py]] - code - tests\test_phone_utils.py
- [[test_phones_match_by_exact_or_last10()]] - code - tests\test_phone_utils.py
- [[verify_guest_flow.py]] - code - scripts\verify_guest_flow.py
- [[Вернуться в админ меню]] - rationale - app\telegram\handlers\settings.py
- [[Добавляет пользователя в БД и обновляет кеш]] - rationale - app\telegram\auth\admin.py
- [[Клавиатура витрины для НЕавторизованного гостя]] - rationale - app\telegram\menus\guest.py
- [[Клавиатура главного меню для АВТОРИЗОВАННОГО гостя]] - rationale - app\telegram\menus\guest.py
- [[Клавиатура для запроса контакта (Login)]] - rationale - app\telegram\menus\guest.py
- [[Обновляет кеш пользователей из БД]] - rationale - app\telegram\auth\admin.py
- [[Проверяет, является ли пользователь авторизованным гостем]] - rationale - app\telegram\auth\admin.py
- [[Удаляет ТОЛЬКО гостя (без риска снести админауборщицу).]] - rationale - app\telegram\auth\admin.py
- [[Удаляет пользователя из БД и обновляет кеш]] - rationale - app\telegram\auth\admin.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/guest.py_/_safe_edit()
SORT file.name ASC
```

## Connections to other communities
- 26 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 9 edges to [[_COMMUNITY_GlobalSetting  global_settings.py]]
- 9 edges to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 6 edges to [[_COMMUNITY_cleaner_task_flow.py  get_all_users()]]
- 3 edges to [[_COMMUNITY_on_startup()  AutoSyncMiddleware]]
- 3 edges to [[_COMMUNITY_str  settings.py]]
- 2 edges to [[_COMMUNITY_houses.py  get_short_description()]]
- 2 edges to [[_COMMUNITY_cleaner.py  show_cleaner_menu()]]
- 1 edge to [[_COMMUNITY_create.py  build_month_keyboard()]]

## Top bridge nodes
- [[admin.py]] - degree 11, connects to 4 communities
- [[guest.py]] - degree 48, connects to 3 communities
- [[_admin_approve_payment()]] - degree 9, connects to 3 communities
- [[start_handler()]] - degree 6, connects to 3 communities
- [[phones_match()]] - degree 9, connects to 2 communities