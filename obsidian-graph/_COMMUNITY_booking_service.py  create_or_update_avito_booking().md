---
type: community
cohesion: 0.06
members: 58
---

# booking_service.py / create_or_update_avito_booking()

**Cohesion:** 0.06 - loosely connected
**Members:** 58 nodes

## Members
- [[.__init__()_3]] - code - tests\test_avito_guest_name_extraction.py
- [[Booking_1]] - code - scripts\verify_availability_logic.py
- [[BookingStatus_1]] - code - scripts\verify_availability_logic.py
- [[PayloadWithDictContact]] - code - tests\test_avito_guest_name_extraction.py
- [[_block_avito_dates()]] - code - app\services\booking_service.py
- [[_cascade_cancel_cleaning()]] - code - app\services\booking_service.py
- [[_make_session()]] - code - tests\test_cleaner_hardening.py
- [[_notify_cleaner_about_cancel()]] - code - app\services\booking_service.py
- [[_safe_background_sheets_sync()]] - code - app\services\booking_service.py
- [[_seed_booking_task()]] - code - tests\test_cleaner_hardening.py
- [[_seed_house_cleaner()]] - code - tests\test_cleaner_hardening.py
- [[_unblock_avito_dates()]] - code - app\services\booking_service.py
- [[booking_service.py]] - code - app\services\booking_service.py
- [[booking_web.py]] - code - app\web\routers\booking_web.py
- [[cancel_booking()]] - code - app\services\booking_service.py
- [[check_availability()]] - code - app\services\booking_service.py
- [[check_availability_new()]] - code - scripts\verify_availability_logic.py
- [[check_availability_old()]] - code - scripts\verify_availability_logic.py
- [[create_booking()_1]] - code - app\web\routers\booking_web.py
- [[create_booking()]] - code - app\services\booking_service.py
- [[create_booking_page()]] - code - app\web\routers\booking_web.py
- [[create_or_update_avito_booking()]] - code - app\services\booking_service.py
- [[create_test_bookings.py]] - code - scripts\create_test_bookings.py
- [[database.py]] - code - app\database.py
- [[delete_booking()]] - code - app\services\booking_service.py
- [[extract_avito_contact_field()]] - code - app\services\avito_sync_service.py
- [[extract_avito_contact_value()]] - code - app\services\booking_service.py
- [[get_all_bookings()]] - code - app\services\booking_service.py
- [[get_available_houses()]] - code - app\services\booking_service.py
- [[get_booking()]] - code - app\services\booking_service.py
- [[get_db()]] - code - app\database.py
- [[init_db()]] - code - app\database.py
- [[list_bookings()]] - code - app\web\routers\booking_web.py
- [[main()_2]] - code - scripts\create_test_bookings.py
- [[main()_6]] - code - scripts\verify_avito_flow.py
- [[run_tests()]] - code - scripts\verify_availability_logic.py
- [[should_replace_avito_guest_value()]] - code - app\services\booking_service.py
- [[sync_all_to_sheets()]] - code - app\services\booking_service.py
- [[test_avito_guest_name_extraction.py]] - code - tests\test_avito_guest_name_extraction.py
- [[test_booking_cancel_propagates_to_active_task()]] - code - tests\test_cleaner_hardening.py
- [[test_booking_cancel_propagates_to_cleaning_task_and_ledger()]] - code - tests\test_cleaner_hardening.py
- [[test_booking_service_extracts_name_from_dict_contact()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_booking_service_falls_back_to_legacy_top_level_fields()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_booking_service_supports_object_contact()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_cleaner_hardening.py]] - code - tests\test_cleaner_hardening.py
- [[test_cleaning_fee_accrued_once_on_done()]] - code - tests\test_cleaner_hardening.py
- [[test_do_not_override_existing_real_guest_name()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_replace_empty_phone_with_incoming_value()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_replace_placeholder_guest_name_with_real_value()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_supply_alert_open_idempotent_and_resolve()]] - code - tests\test_cleaner_hardening.py
- [[test_sync_service_extracts_name_from_dict_contact()]] - code - tests\test_avito_guest_name_extraction.py
- [[test_sync_service_falls_back_to_legacy_top_level_fields()]] - code - tests\test_avito_guest_name_extraction.py
- [[update_booking()_1]] - code - app\web\routers\booking_web.py
- [[update_booking()]] - code - app\services\booking_service.py
- [[verify_availability_logic.py]] - code - scripts\verify_availability_logic.py
- [[verify_avito_flow.py]] - code - scripts\verify_avito_flow.py
- [[view_booking()]] - code - app\web\routers\booking_web.py
- [[Создание тестовых броней для проверки фильтров]] - rationale - scripts\create_test_bookings.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/booking_service.py_/_create_or_update_avito_booking()
SORT file.name ASC
```

## Connections to other communities
- 29 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 5 edges to [[_COMMUNITY_test_avito_overlap_guard.py  process_avito_booking()]]
- 2 edges to [[_COMMUNITY_str  settings.py]]
- 2 edges to [[_COMMUNITY_create.py  build_month_keyboard()]]
- 1 edge to [[_COMMUNITY_on_startup()  AutoSyncMiddleware]]

## Top bridge nodes
- [[create_or_update_avito_booking()]] - degree 11, connects to 3 communities
- [[Booking_1]] - degree 9, connects to 2 communities
- [[should_replace_avito_guest_value()]] - degree 7, connects to 2 communities
- [[BookingStatus_1]] - degree 5, connects to 2 communities
- [[extract_avito_contact_field()]] - degree 5, connects to 2 communities