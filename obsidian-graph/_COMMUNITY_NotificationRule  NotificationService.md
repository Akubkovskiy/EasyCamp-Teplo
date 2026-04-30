---
type: community
cohesion: 0.10
members: 27
---

# NotificationRule / NotificationService

**Cohesion:** 0.10 - loosely connected
**Members:** 27 nodes

## Members
- [[._notify_admins()]] - code - app\services\notification_service.py
- [[._notify_cleaners()]] - code - app\services\notification_service.py
- [[._notify_guests()]] - code - app\services\notification_service.py
- [[.process_rule()]] - code - app\services\notification_service.py
- [[NotificationRule]] - code - app\services\notification_service.py
- [[NotificationService]] - code - app\services\notification_service.py
- [[check_and_notify_cleaners()]] - code - app\jobs\cleaning_notifier.py
- [[check_and_notify_guests()]] - code - app\jobs\guest_notifier.py
- [[cleaning_notifier.py]] - code - app\jobs\cleaning_notifier.py
- [[format_checkin_message()]] - code - app\jobs\guest_notifier.py
- [[format_checkout_message()]] - code - app\jobs\guest_notifier.py
- [[format_cleaning_keyboard()]] - code - app\jobs\cleaning_notifier.py
- [[format_cleaning_message()]] - code - app\jobs\cleaning_notifier.py
- [[format_welcome_message()]] - code - app\jobs\guest_notifier.py
- [[guest_notifier.py]] - code - app\jobs\guest_notifier.py
- [[notification_service.py]] - code - app\services\notification_service.py
- [[test_cleaning_notify()]] - code - app\telegram\handlers\settings.py
- [[Запуск проверки уведомлений для гостей]] - rationale - app\jobs\guest_notifier.py
- [[Проверяет выезды на ЗАВТРА и уведомляет уборщиц через Service]] - rationale - app\jobs\cleaning_notifier.py
- [[Сообщение в день выезда]] - rationale - app\jobs\guest_notifier.py
- [[Сообщение в день заезда]] - rationale - app\jobs\guest_notifier.py
- [[Сообщение за 2 дня до заезда]] - rationale - app\jobs\guest_notifier.py
- [[Тестовый запуск уведомлений]] - rationale - app\telegram\handlers\settings.py
- [[Уведомление гостей (персонально каждому)]] - rationale - app\services\notification_service.py
- [[Уведомление уборщиц (одна сущность 'смена' на всех, или каждому по копии)]] - rationale - app\services\notification_service.py
- [[Формирует клавиатуру подтверждения]] - rationale - app\jobs\cleaning_notifier.py
- [[Формирует сообщение для уборщицы]] - rationale - app\jobs\cleaning_notifier.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/NotificationRule_/_NotificationService
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 1 edge to [[_COMMUNITY_str  settings.py]]

## Top bridge nodes
- [[NotificationRule]] - degree 14, connects to 1 community
- [[NotificationService]] - degree 10, connects to 1 community
- [[test_cleaning_notify()]] - degree 3, connects to 1 community
- [[Формирует сообщение для уборщицы]] - degree 3, connects to 1 community
- [[Формирует клавиатуру подтверждения]] - degree 3, connects to 1 community