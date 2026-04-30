---
type: community
cohesion: 0.03
members: 104
---

# create.py / build_month_keyboard()

**Cohesion:** 0.03 - loosely connected
**Members:** 104 nodes

## Members
- [[AvailabilityState]] - code - app\telegram\state\availability.py
- [[BookingStates]] - code - app\telegram\states\booking.py
- [[FSM состояния для управления бронированием]] - rationale - app\telegram\states\booking.py
- [[__init__.py_7]] - code - app\telegram\handlers\booking_management\__init__.py
- [[_back_cb()]] - code - app\telegram\handlers\availability.py
- [[availability.py]] - code - app\telegram\handlers\availability.py
- [[availability.py_1]] - code - app\telegram\state\availability.py
- [[availability_command()]] - code - app\telegram\handlers\availability.py
- [[back_to_checkout_selection()]] - code - app\telegram\handlers\booking_management\create.py
- [[back_to_confirmation_screen()]] - code - app\telegram\handlers\booking_management\create.py
- [[back_to_guests_count_input()]] - code - app\telegram\handlers\booking_management\create.py
- [[back_to_name_input()]] - code - app\telegram\handlers\booking_management\create.py
- [[back_to_phone_input()]] - code - app\telegram\handlers\booking_management\create.py
- [[booking.py_1]] - code - app\telegram\states\booking.py
- [[build_month_keyboard()]] - code - app\telegram\ui\calendar.py
- [[build_year_keyboard()]] - code - app\telegram\ui\calendar.py
- [[calendar.py]] - code - app\domain\calendar.py
- [[calendar.py_1]] - code - app\telegram\ui\calendar.py
- [[cancel_creation()]] - code - app\telegram\handlers\booking_management\create.py
- [[cancel_edit_booking()]] - code - app\telegram\handlers\booking_management\edit.py
- [[change_bookin_month()]] - code - app\telegram\handlers\booking_management\create.py
- [[change_bookout_month()]] - code - app\telegram\handlers\booking_management\create.py
- [[change_checkin_month()]] - code - app\telegram\handlers\availability.py
- [[change_checkout_month()]] - code - app\telegram\handlers\availability.py
- [[change_ebin_month()]] - code - app\telegram\handlers\booking_management\edit.py
- [[change_ebout_month()]] - code - app\telegram\handlers\booking_management\edit.py
- [[change_pick_year()]] - code - app\telegram\handlers\availability.py
- [[cmd_dates()]] - code - app\telegram\handlers\guest.py
- [[confirm_booking()]] - code - app\telegram\handlers\booking_management\create.py
- [[create.py]] - code - app\telegram\handlers\booking_management\create.py
- [[edit.py]] - code - app\telegram\handlers\booking_management\edit.py
- [[execute_cancel()]] - code - app\telegram\handlers\booking_management\view.py
- [[execute_delete()]] - code - app\telegram\handlers\booking_management\view.py
- [[format_phone()_1]] - code - app\web\routers\booking_web.py
- [[format_phone()]] - code - app\utils\validators.py
- [[get_month_dates()]] - code - app\domain\calendar.py
- [[guest_name_entered()]] - code - app\telegram\handlers\booking_management\create.py
- [[guest_phone_entered()]] - code - app\telegram\handlers\booking_management\create.py
- [[guests_count_entered()]] - code - app\telegram\handlers\booking_management\create.py
- [[house_selected()]] - code - app\telegram\handlers\booking_management\create.py
- [[ignore_calendar_click()]] - code - app\telegram\handlers\booking_management\create.py
- [[ignore_callback()]] - code - app\telegram\handlers\availability.py
- [[main()_4]] - code - scripts\standardize_phones.py
- [[month_title()]] - code - app\telegram\ui\calendar.py
- [[pick_bookin_month_year()]] - code - app\telegram\handlers\booking_management\create.py
- [[pick_bookout_month_year()]] - code - app\telegram\handlers\booking_management\create.py
- [[prepayment_entered()]] - code - app\telegram\handlers\booking_management\create.py
- [[process_edit_count()]] - code - app\telegram\handlers\booking_management\edit.py
- [[process_edit_name()_1]] - code - app\telegram\handlers\booking_management\edit.py
- [[process_edit_phone()]] - code - app\telegram\handlers\booking_management\edit.py
- [[process_edit_price()]] - code - app\telegram\handlers\booking_management\edit.py
- [[process_edit_status()]] - code - app\telegram\handlers\booking_management\edit.py
- [[remainder_entered()]] - code - app\telegram\handlers\booking_management\create.py
- [[render_booking_card()]] - code - app\telegram\handlers\booking_management\view.py
- [[request_cancel_confirmation()]] - code - app\telegram\handlers\booking_management\view.py
- [[request_delete_confirmation()]] - code - app\telegram\handlers\booking_management\view.py
- [[select_checkin_date()_1]] - code - app\telegram\handlers\booking_management\create.py
- [[select_checkin_date()]] - code - app\telegram\handlers\availability.py
- [[select_checkout_date()_1]] - code - app\telegram\handlers\booking_management\create.py
- [[select_checkout_date()]] - code - app\telegram\handlers\availability.py
- [[select_edit_checkin_date()]] - code - app\telegram\handlers\booking_management\edit.py
- [[select_edit_checkout_date()]] - code - app\telegram\handlers\booking_management\edit.py
- [[send_booking_details_refreshed()]] - code - app\telegram\handlers\booking_management\edit.py
- [[show_edit_menu()]] - code - app\telegram\handlers\booking_management\edit.py
- [[standardize_phones.py]] - code - scripts\standardize_phones.py
- [[start_availability()]] - code - app\telegram\handlers\availability.py
- [[start_booking_from_availability()]] - code - app\telegram\handlers\booking_management\create.py
- [[start_editing_field()]] - code - app\telegram\handlers\booking_management\edit.py
- [[start_new_booking()]] - code - app\telegram\handlers\booking_management\create.py
- [[start_pick_month()]] - code - app\telegram\handlers\availability.py
- [[status_selected()]] - code - app\telegram\handlers\booking_management\create.py
- [[validate_dates()_1]] - code - app\utils\validators.py
- [[validate_phone()]] - code - app\utils\validators.py
- [[validators.py]] - code - app\utils\validators.py
- [[view.py]] - code - app\telegram\handlers\booking_management\view.py
- [[view_booking_details()]] - code - app\telegram\handlers\booking_management\view.py
- [[Валидация дат заезда и выезда     Возвращает (is_valid, error_message)]] - rationale - app\utils\validators.py
- [[Валидация номера телефона.     Поддерживает форматы +79991234567, 89991234567,]] - rationale - app\utils\validators.py
- [[Возврат к вводу имени гостя]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Возврат к вводу количества гостей]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Возврат к вводу телефона]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Возврат к выбору даты выезда]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Возврат к экрану подтверждения]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Дата выезда выбрана - Проверка и ввод имени]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Дата заезда выбрана - Календарь выезда]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Домик выбран - Календарь заезда]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Запрос подтверждения отмены]] - rationale - app\telegram\handlers\booking_management\view.py
- [[Запрос подтверждения удаления]] - rationale - app\telegram\handlers\booking_management\view.py
- [[Клавиатура выбора месяца]] - rationale - app\telegram\ui\calendar.py
- [[Начало бронирования из проверки доступности]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Начало создания новой брони]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Обработчик выбора даты выезда]] - rationale - app\telegram\handlers\availability.py
- [[Обработчик выбора даты заезда]] - rationale - app\telegram\handlers\availability.py
- [[Обработчик для неактивных кнопок (дни недели, пустые ячейки)]] - rationale - app\telegram\handlers\availability.py
- [[Обработчик команды availability для проверки доступности домиков]] - rationale - app\telegram\handlers\availability.py
- [[Обработчики для ПРОСМОТРА и ОТМЕНЫ бронирований]] - rationale - app\telegram\handlers\booking_management\view.py
- [[Обработчики для СОЗДАНИЯ бронирований]] - rationale - app\telegram\handlers\booking_management\create.py
- [[Отрисовка карточки брони (общая логика)]] - rationale - app\telegram\handlers\booking_management\view.py
- [[Переключение месяца при выборе даты выезда]] - rationale - app\telegram\handlers\availability.py
- [[Просмотр деталей брони]] - rationale - app\telegram\handlers\booking_management\view.py
- [[Скрипт для стандартизации телефонных номеров в базе данных Приводит все номера]] - rationale - scripts\standardize_phones.py
- [[Стандартизация телефонных номеров]] - rationale - scripts\standardize_phones.py
- [[Утилиты валидации данных]] - rationale - app\utils\validators.py
- [[Форматирование телефона в стандартный вид +7 (XXX) XXX-XX-XX]] - rationale - app\utils\validators.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/create.py_/_build_month_keyboard()
SORT file.name ASC
```

## Connections to other communities
- 56 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 3 edges to [[_COMMUNITY_is_admin()  guest_booking.py]]
- 2 edges to [[_COMMUNITY_booking_service.py  create_or_update_avito_booking()]]
- 1 edge to [[_COMMUNITY_str  settings.py]]
- 1 edge to [[_COMMUNITY_houses.py  get_short_description()]]
- 1 edge to [[_COMMUNITY_test_avito_overlap_guard.py  process_avito_booking()]]
- 1 edge to [[_COMMUNITY_guest.py  safe_edit()]]
- 1 edge to [[_COMMUNITY_houses.py  HouseUpdate]]

## Top bridge nodes
- [[format_phone()_1]] - degree 7, connects to 3 communities
- [[BookingStates]] - degree 17, connects to 2 communities
- [[select_checkout_date()]] - degree 4, connects to 2 communities
- [[cmd_dates()]] - degree 3, connects to 2 communities
- [[build_month_keyboard()]] - degree 18, connects to 1 community