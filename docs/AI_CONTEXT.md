> ⚠️ **SUPERSEDED (2026-04-27).** This file's directory structure is out of date (e.g. references `app/db/models.py` and `app/handlers/` which no longer exist). For current context entry, use:
>
> - `EasyCamp-Teplo/CLAUDE.md` — repo guidance
> - `EasyCamp-Teplo/STATUS.md` — state snapshot
> - `EasyCamp-Teplo/INDEX.md` — by-task routing
> - `docs/OBSIDIAN_EASYCAMP_INDEX_2026-02-27.md` — code-level architecture map
> - `.claude/skills/project-discovery/SKILL.md` — fixed entry order
>
> Kept for historical reference only. Do not use as primary onboarding doc.

---

# Файлы для погружения AI в контекст проекта EasyCamp-Teplo (LEGACY 2025)

## 📋 Обязательные файлы (минимальный контекст)

### 1. Документация проекта

```
README.md                          # Общее описание проекта
docs/DEPLOYMENT.md                 # Инструкции по развертыванию
docs/architecture.md               # Архитектура (если есть)
docs/roadmap.md                    # Дорожная карта развития
```

### 2. Конфигурация

```
.env.example                       # Пример переменных окружения
requirements.txt                   # Зависимости Python
```

### 3. Основные модули

```
app/main.py                        # Точка входа приложения
app/core/config.py                 # Конфигурация
app/models.py                      # Модели базы данных
app/database.py                    # Настройка БД
```

### 4. Telegram Bot

```
app/telegram/handlers/admin_menu.py      # Главное меню админа
app/telegram/handlers/availability.py    # Календарь и доступность
app/telegram/handlers/bookings.py        # Управление бронями
app/telegram/handlers/contacts.py        # Контактная информация
app/telegram/menus/admin.py              # Клавиатуры меню
app/telegram/ui/calendar.py              # UI календаря
```

### 5. Сервисы

```
app/services/booking_service.py    # Логика работы с бронями
app/avito/webhook.py                # Webhook от Avito
app/avito/schemas.py                # Схемы данных Avito
```

---

## 📚 Расширенный контекст (для глубокого понимания)

### Дополнительные файлы

```
app/telegram/notifier.py           # Уведомления в Telegram
app/telegram/state/availability.py # Состояние для календаря
scripts/create_test_bookings.py    # Скрипт создания тестовых данных
scripts/verify_avito_flow.py       # Проверка Avito интеграции
```

---

## 🎯 Рекомендуемый порядок загрузки

### Шаг 1: Общий контекст (3 файла)

1. `README.md` - что это за проект
2. `docs/DEPLOYMENT.md` - как развернуть
3. `docs/roadmap.md` - планы развития

### Шаг 2: Архитектура (5 файлов)

4. `app/main.py` - точка входа
5. `app/core/config.py` - настройки
6. `app/models.py` - структура данных
7. `app/database.py` - работа с БД
8. `requirements.txt` - зависимости

### Шаг 3: Функционал (7 файлов)

 9. `app/telegram/handlers/admin_menu.py`
10. `app/telegram/handlers/bookings.py`
11. `app/telegram/handlers/availability.py`
12. `app/telegram/handlers/contacts.py`
13. `app/services/booking_service.py`
14. `app/avito/webhook.py`
15. `app/telegram/ui/calendar.py`

---

## 💡 Что НЕ нужно отправлять

❌ `.env` - содержит секретные данные ❌ `easycamp.db` - база данных ❌ `google-credentials.json` - секретные ключи ❌ `__pycache__/` - кэш Python ❌ `.git/` - история Git

---

## 📝 Пример промпта для AI

```
Привет! Помоги мне с проектом EasyCamp-Teplo.

Это Telegram бот для управления базой отдыха в Архызе.

Прикрепляю ключевые файлы для контекста:
1. README.md - описание проекта
2. docs/DEPLOYMENT.md - инструкции
3. app/main.py - точка входа
4. app/models.py - модели данных
5. app/telegram/handlers/bookings.py - обработчики броней

Мне нужно [опишите вашу задачу]...
```

---

## 🔧 Альтернатива: Создать сводный документ

Вместо отправки множества файлов, можно создать один сводный документ:

```markdown
# Контекст проекта EasyCamp-Teplo

## Описание
[Скопировать из README.md]

## Архитектура
- FastAPI + Telegram Bot (aiogram)
- SQLite база данных
- Avito webhook интеграция
- Google Sheets синхронизация (в разработке)

## Основные модели
[Скопировать из app/models.py]

## Текущий функционал
1. Telegram бот с админ-панелью
2. Управление бронями (просмотр, фильтры)
3. Календарь для выбора дат
4. Webhook от Avito
5. Контактная информация

## Структура кода
app/
├── main.py              # Точка входа
├── models.py            # Модели БД
├── telegram/
│   ├── handlers/        # Обработчики команд
│   └── ui/              # UI компоненты
└── services/            # Бизнес-логика
```

---

## ✅ Итоговая рекомендация

**Минимальный набор (5-7 файлов):**

1. [README.md](http://README.md)
2. docs/DEPLOYMENT.md
3. app/main.py
4. app/models.py
5. app/telegram/handlers/bookings.py
6. app/telegram/handlers/availability.py
7. app/services/booking_service.py

Этого достаточно для понимания структуры и основного функционала.

**Для конкретных задач добавляйте:**

- Работа с календарем → `app/telegram/ui/calendar.py`
- Avito интеграция → `app/avito/webhook.py`, `app/avito/schemas.py`
- Google Sheets → `docs/google_sheets_setup.md`, `implementation_plan.md`
