---
type: community
cohesion: 0.04
members: 68
---

# GlobalSetting / global_settings.py

**Cohesion:** 0.04 - loosely connected
**Members:** 68 nodes

## Members
- [[ContentSettingsState]] - code - app\telegram\handlers\settings_content.py
- [[GlobalSetting]] - code - app\models.py
- [[Helper for specifically fetching project identity]] - rationale - app\services\settings_service.py
- [[Idempotent upsert. Caller отвечает за commit.]] - rationale - app\services\global_settings.py
- [[Merges environment settings with database GlobalSettings.         DB settings t]] - rationale - app\services\settings_service.py
- [[Pure-функция для тестов гость может сам отменить бронь, только     если до заез]] - rationale - app\services\global_settings.py
- [[Pure-функция для тестов инструкция доступна, если до заезда     осталось = `op]] - rationale - app\services\global_settings.py
- [[Pure определить стадию оплаты.     - no_payment — ничего не оплачено, ждём за]] - rationale - app\services\global_settings.py
- [[SetupStateService]] - code - app\services\setup_service.py
- [[Unit-тесты для pure-функций конфигурируемых правил гостя (Phase G10.3). DB не ну]] - rationale - tests\test_guest_settings.py
- [[can_guest_self_cancel()]] - code - app\services\global_settings.py
- [[cancel_content_edit()]] - code - app\telegram\handlers\settings_content.py
- [[check_secret()]] - code - app\web\routers\setup_web.py
- [[content_menu()]] - code - app\telegram\handlers\settings_content.py
- [[get_guest_cancel_window_days()]] - code - app\services\global_settings.py
- [[get_guest_instruction_open_hours()]] - code - app\services\global_settings.py
- [[get_int()]] - code - app\services\global_settings.py
- [[get_str()]] - code - app\services\global_settings.py
- [[global_settings.py]] - code - app\services\global_settings.py
- [[guest_cancel_confirm()]] - code - app\telegram\handlers\guest_booking.py
- [[is_initial_setup_done()]] - code - app\services\setup_service.py
- [[is_instruction_open()]] - code - app\services\global_settings.py
- [[payment_stage()]] - code - app\services\global_settings.py
- [[process_content_edit()]] - code - app\telegram\handlers\settings_content.py
- [[reset_state()]] - code - scripts\verify_gates_c3.py
- [[reset_state()_1]] - code - scripts\verify_wizard.py
- [[run_server()]] - code - scripts\verify_gates_c3.py
- [[run_server()_6]] - code - scripts\verify_wizard.py
- [[run_verification_gates()]] - code - scripts\verify_gates_c3.py
- [[set_initial_setup_done()]] - code - app\services\setup_service.py
- [[set_value()]] - code - app\services\global_settings.py
- [[settings_content.py]] - code - app\telegram\handlers\settings_content.py
- [[setup_page()]] - code - app\web\routers\setup_web.py
- [[setup_service.py]] - code - app\services\setup_service.py
- [[setup_web.py]] - code - app\web\routers\setup_web.py
- [[start_edit_content()]] - code - app\telegram\handlers\settings_content.py
- [[step1_page()]] - code - app\web\routers\setup_web.py
- [[step1_save()]] - code - app\web\routers\setup_web.py
- [[step2_page()]] - code - app\web\routers\setup_web.py
- [[step2_save()]] - code - app\web\routers\setup_web.py
- [[step3_page()]] - code - app\web\routers\setup_web.py
- [[step3_save()]] - code - app\web\routers\setup_web.py
- [[test_cancel_inside_window_blocked()]] - code - tests\test_guest_settings.py
- [[test_cancel_outside_window_allowed()]] - code - tests\test_guest_settings.py
- [[test_cancel_window_zero_means_never_self_cancel_for_today()]] - code - tests\test_guest_settings.py
- [[test_cancel_zero_days_blocked()]] - code - tests\test_guest_settings.py
- [[test_custom_window_48_hours()]] - code - tests\test_guest_settings.py
- [[test_guest_settings.py]] - code - tests\test_guest_settings.py
- [[test_instruction_closed_far_in_future()]] - code - tests\test_guest_settings.py
- [[test_instruction_open_at_window_boundary()]] - code - tests\test_guest_settings.py
- [[test_instruction_open_close_to_checkin()]] - code - tests\test_guest_settings.py
- [[test_instruction_open_when_already_started()]] - code - tests\test_guest_settings.py
- [[test_wizard_flow()]] - code - scripts\verify_wizard.py
- [[verify_gates_c3.py]] - code - scripts\verify_gates_c3.py
- [[verify_wizard.py]] - code - scripts\verify_wizard.py
- [[За сколько часов до заезда открывается инструкция по заселению.]] - rationale - app\services\global_settings.py
- [[Окно отмены брони (в днях до заезда), в течение которого гость     может отменит]] - rationale - app\services\global_settings.py
- [[Проверка секрета и старт сессии]] - rationale - app\web\routers\setup_web.py
- [[Проверяет, завершена ли первоначальная настройка.         Флаг 'initial_setup_d]] - rationale - app\services\setup_service.py
- [[Создание админа и Завершение]] - rationale - app\web\routers\setup_web.py
- [[Сохранение шага 1 - Переход к Шагу 2]] - rationale - app\web\routers\setup_web.py
- [[Сохранение шага 2 - Завершение]] - rationale - app\web\routers\setup_web.py
- [[Страница первого запуска (ввод секрета)]] - rationale - app\web\routers\setup_web.py
- [[Тонкий хелпер чтениязаписи `GlobalSetting` с типизацией.  Используется guest-fl]] - rationale - app\services\global_settings.py
- [[Устанавливает флаг завершения настройки.]] - rationale - app\services\setup_service.py
- [[Читает int из GlobalSetting. Если значение пустое или нечисловое —     возвращае]] - rationale - app\services\global_settings.py
- [[Шаг 1 Идентичность проекта]] - rationale - app\web\routers\setup_web.py
- [[Шаг 3 Создание Администратора]] - rationale - app\web\routers\setup_web.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GlobalSetting_/_global_settings.py
SORT file.name ASC
```

## Connections to other communities
- 32 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 9 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 4 edges to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 2 edges to [[_COMMUNITY_login()  get_password_hash()]]
- 2 edges to [[_COMMUNITY_str  settings.py]]
- 1 edge to [[_COMMUNITY_cleaner_task_flow.py  get_all_users()]]
- 1 edge to [[_COMMUNITY_houses.py  HouseUpdate]]

## Top bridge nodes
- [[GlobalSetting]] - degree 47, connects to 4 communities
- [[guest_cancel_confirm()]] - degree 6, connects to 4 communities
- [[step3_save()]] - degree 4, connects to 2 communities
- [[global_settings.py]] - degree 11, connects to 1 community
- [[SetupStateService]] - degree 9, connects to 1 community