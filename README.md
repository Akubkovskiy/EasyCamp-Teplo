# EasyCamp-Teplo

[![CI](https://github.com/Akubkovskiy/EasyCamp-Teplo/actions/workflows/ci.yml/badge.svg)](https://github.com/Akubkovskiy/EasyCamp-Teplo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

**B2B SaaS‑платформа для автоматизации управления базой отдыха. MVP-пример — база отдыха «Тепло» в Архызе, КЧР.**

## 🏕 Кратко о проекте

EasyCamp — это open-source платформа, которую ты можешь настроить для своей базы отдыха, чтобы:
- автоматизировать бронирование (через Telegram, Авито и др. каналы)
- упростить управление домами, бронированиями, сотрудниками
- интегрировать CRM, платежные сервисы, уведомления

Вся архитектура построена так, чтобы учиться на реальном бизнесе и масштабировать решение под другие объекты отдыха.

## 🚀 Быстрый старт

**Новый проект?** Следуйте подробному руководству по развертыванию:
👉 **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** 👈

Время развертывания: ~20-30 минут

### Краткая инструкция

```bash
# 1. Клонировать и установить
git clone https://github.com/Akubkovskiy/EasyCamp-Teplo.git
cd EasyCamp-Teplo
pip install -r requirements.txt

# 2. Настроить .env (см. .env.example)
cp .env.example .env
# Заполните переменные в .env

# 3. Запустить
python -m uvicorn app.main:app --reload
```

Подробные инструкции по настройке Google Sheets API, Telegram Bot и других сервисов - в [DEPLOYMENT.md](docs/DEPLOYMENT.md).

## 📋 Основные возможности

### Синхронизация данных
- 🔄 **Автоматическая синхронизация**: Данные обновляются при каждом обращении к боту (умное кэширование)
- ⏱ **Периодическая синхронизация**: Фоновое обновление каждые 5 минут
- 🚀 **При старте**: Актуализация данных сразу после запуска бота
- 🛡 **Защита**: Умная система предотвращает превышение лимитов API Google

### Управление бронями
- Полная синхронизация с Avito API (включая неподтвержденные брони)
- Удобный календарь с выбором дат и навигацией по месяцам
- Просмотр занятости и списка заездов
- Автоматические уведомления о новых и обновленных бронях

### Telegram бот
- Админ-панель для управления бронями и домиками
- Гостевое меню для проверки доступности
- Интерактивные календари и формы
- Команды: `/start`, `/sync`, `/fetch_avito`, `/availability`

## 🔧 Технологии

- **Backend**: Python 3.11+, FastAPI, aiogram 3.x
- **База данных**: SQLite (SQLAlchemy ORM)
- **Интеграции**: 
  - Google Sheets API (синхронизация данных)
  - Telegram Bot API (интерфейс управления)
  - Avito API (автоматическая синхронизация броней)
- **Планировщик**: APScheduler (фоновые задачи)

## 📚 Документация

- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — полное руководство по развертыванию
- [Architecture](docs/architecture.md) — техническая структура и схемы сервисов
- [Roadmap](docs/roadmap.md) — стратегическое развитие и MVP-этапы
- [Google Sheets Setup](docs/google_sheets_setup.md) — настройка интеграции с Google Sheets
- [Ideas Log](docs/ideas_log.md) — идеи, расширения, брейншторминг

## 📱 Связь и автор

- Алексей Кубковский (РФ, Архыз)
- [Telegram](https://t.me/Alexey_kubkovskiy) / [Email](mailto:akubkovskiy@gmail.com)

## ⚠️ Статус

> Проект находится в активной доработке. MVP готовится на базе отдыха «Тепло». Все консультации и помощь приветствуются!

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up the project locally and submit improvements.

## 📄 License

[MIT](LICENSE) © Alexey Kubkovskiy
