# EasyCamp-Teplo

**B2B SaaS‑платформа для автоматизации управления базой отдыха. MVP-пример — база отдыха «Тепло» в Архызе, КЧР.**

## 🏕 Кратко о проекте

EasyCamp — это open-source платформа, которую ты можешь настроить для своей базы отдыха, чтобы:
- автоматизировать бронирование (через Telegram, Авито и др. каналы)
- упростить управление домами, бронированиями, сотрудниками
- интегрировать CRM, платежные сервисы, уведомления

Вся архитектура построена так, чтобы учиться на реальном бизнесе и масштабировать решение под другие объекты отдыха.

## 🚀 Возможности MVP

- Синхронизация данных через Google Sheets и Firestore
- Telegram Bot для гостей и сотрудников
- Обработка бронирований и платежей через CloudPayments
- Уведомления, задачи, расписание для сотрудников
- Быстрое развертывание через Docker

## 🔧 Технологии

- Python (основной язык)
- Firestore (NoSQL база)
- Google Sheets API (импорт/экспорт)
- Telegram API (бот)
- CloudPayments API
- Docker, docker-compose для оркестрации
- Возможна интеграция с Авито (iCal)

## ⚡️ Быстрый старт

1. Клонируй репозиторий:
    ```
    git clone https://github.com/USERNAME/easycamp-teplo.git
    ```
2. Перейди в папку, создай `.env` по примеру из [setup_instructions.md](docs/setup_instructions.md).
3. Установи зависимости:
    ```
    pip install -r requirements.txt
    ```
4. Запусти через Docker (или локально — подробности в [setup_instructions.md](docs/setup_instructions.md)).

## 📚 Документация

- [Roadmap](docs/roadmap.md) — стратегическое развитие и MVP-этапы
- [Architecture](docs/architecture.md) — техническая структура и схемы сервисов
- [Setup Instructions](docs/setup_instructions.md) — как развернуть систему
- [Ideas Log](docs/ideas_log.md) — идеи, расширения, брейншторминг

## 📝 Структура переменных окружения (.env)
- Пример: ADMINTGID, TGBOTTOKEN, GCPSHEETSSERVICEACCOUNTJSONPATH и другие ключи — детали в setup_instructions.md

## 📱 Связь и автор

- Алексей Кубковский (РФ, Архыз)
- [Telegram](#) / [email](mailto:akubkovskiy@gmail.com)

## ⚠️ Статус

> Проект находится в активной доработке. MVP готовится на базе отдыха «Тепло». Все консультации и помощь приветствуются!
