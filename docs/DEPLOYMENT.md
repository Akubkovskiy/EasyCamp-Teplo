# 🚀 Руководство по развертыванию EasyCamp-Teplo

Это руководство поможет быстро развернуть проект на новом окружении.

---

## 📋 Содержание

1. [Базовая настройка](#базовая-настройка)
2. [Google Sheets API](#google-sheets-api)
3. [Telegram Bot](#telegram-bot)
4. [Avito Integration](#avito-integration)
5. [Запуск проекта](#запуск-проекта)

---

## Базовая настройка

<details>
<summary><b>Шаг 1: Клонирование и установка зависимостей</b></summary>

### 1.1 Клонировать репозиторий
```bash
git clone https://github.com/Akubkovskiy/EasyCamp-Teplo.git
cd EasyCamp-Teplo
```

### 1.2 Создать виртуальное окружение
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 1.3 Установить зависимости
```bash
pip install -r requirements.txt
```

### 1.4 Создать файл .env
```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

</details>

---

## Google Sheets API

<details>
<summary><b>Шаг 2: Настройка Google Cloud Project</b></summary>

### 2.1 Создание проекта

1. Перейдите на https://console.cloud.google.com/
2. Нажмите **"Select a project"** → **"New Project"**
3. Название проекта: `EasyCamp-Teplo`
4. Нажмите **"Create"**

### 2.2 Включение Google Sheets API

1. В меню слева: **"APIs & Services"** → **"Library"**
2. Найдите **"Google Sheets API"**
3. Нажмите **"Enable"**

### 2.3 Создание Service Account

1. **"APIs & Services"** → **"Credentials"**
2. **"Create Credentials"** → **"Service Account"**
3. Заполните:
   - **Service account name:** `easycamp-sheets-bot`
   - **Service account ID:** `easycamp-sheets-bot`
   - **Description:** `Bot for syncing bookings with Google Sheets`
4. **"Create and Continue"**
5. **Role:** Editor (или пропустить)
6. **"Done"**

### 2.4 Создание и сохранение ключа

1. Найдите Service Account в списке
2. Нажмите на него → вкладка **"Keys"**
3. **"Add Key"** → **"Create new key"**
4. Тип: **JSON**
5. **"Create"** (файл скачается автоматически)

### 2.5 Сохранение ключа в проект

1. Переименуйте скачанный файл в `google-credentials.json`
2. Поместите в корень проекта: `EasyCamp-Teplo/google-credentials.json`
3. ⚠️ **Файл уже в .gitignore, не коммитьте его!**

</details>

<details>
<summary><b>Шаг 3: Создание Google Таблицы</b></summary>

### 3.1 Создание таблицы

1. Откройте https://sheets.google.com/
2. Создайте новую таблицу
3. Название: **"EasyCamp Teplo - Брони"**

### 3.2 Получение ID таблицы

Скопируйте ID из URL:
```
https://docs.google.com/spreadsheets/d/[ВОТ_ЭТОТ_ID]/edit
                                        ^^^^^^^^^^^^^^^^
```

### 3.3 Предоставление доступа

1. В таблице нажмите **"Share"** (Поделиться)
2. Вставьте email Service Account из файла `google-credentials.json`:
   - Найдите поле `"client_email"`
   - Например: `easycamp-sheets-bot@easycamp-teplo.iam.gserviceaccount.com`
3. Права: **Editor**
4. Снимите галочку **"Notify people"**
5. **"Share"**

### 3.4 Добавление в .env

Откройте `.env` и добавьте:
```env
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=ваш_id_таблицы_из_шага_3.2
```

</details>

---

## Telegram Bot

<details>
<summary><b>Шаг 4: Создание Telegram бота</b></summary>

### 4.1 Создание бота через BotFather

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Введите имя бота (например: `EasyCamp Teplo Bot`)
4. Введите username (например: `easycamp_teplo_bot`)
5. **Скопируйте токен** (выглядит как `1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### 4.2 Получение Chat ID

1. Напишите боту любое сообщение
2. Откройте в браузере:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```
3. Найдите `"chat":{"id":572840161}` - это ваш Chat ID

### 4.3 Добавление в .env

```env
TELEGRAM_BOT_TOKEN=ваш_токен_из_шага_4.1
TELEGRAM_CHAT_ID=ваш_chat_id_из_шага_4.2

# Настройки синхронизации (опционально)
ENABLE_AUTO_SYNC=true
SYNC_ON_BOT_START=true
SYNC_ON_USER_INTERACTION=true
SYNC_CACHE_TTL_SECONDS=30
```

</details>

---

## Avito Integration

<details>
<summary><b>Шаг 5: Настройка Avito Webhook (опционально)</b></summary>

### 5.1 Получение API ключей Avito

1. Войдите в личный кабинет Avito
2. Перейдите в раздел **"API"** или **"Интеграции"**
3. Создайте новое приложение
4. Скопируйте:
   - **Client ID**
   - **Client Secret**

### 5.2 Настройка Webhook

1. В настройках Avito API укажите URL webhook:
   ```
   https://ваш-домен.com/avito/webhook
   ```
2. Выберите события для отправки (новые брони, изменения статуса)

### 5.3 Добавление в .env

```env
AVITO_CLIENT_ID=ваш_client_id
AVITO_CLIENT_SECRET=ваш_client_secret
```

⚠️ **Примечание:** Для локальной разработки используйте ngrok или аналог для публичного URL.

</details>

---

## Запуск проекта

<details>
<summary><b>Шаг 6: Запуск бота</b></summary>

### 6.1 Проверка .env

Убедитесь что `.env` содержит все необходимые переменные:
```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=...
```

### 6.2 Инициализация базы данных

База создается автоматически при первом запуске.

### 6.3 Запуск бота

**Windows:**
```bash
start_bot.bat
```

**Или вручную:**
```bash
python -m uvicorn app.main:app --reload
```

### 6.4 Проверка работы

1. Откройте Telegram и найдите вашего бота
2. Отправьте команду `/start`
3. Должно появиться меню с кнопками

</details>

<details>
<summary><b>Шаг 7: Создание тестовых данных</b></summary>

### 7.1 Запуск скрипта создания тестовых броней

```bash
python scripts/create_test_bookings.py
```

### 7.2 Проверка в боте

1. Отправьте команду `/broni` или "брони"
2. Выберите "Все активные"
3. Должны отобразиться тестовые брони

### 7.3 Проверка синхронизации с Google Sheets

1. Отправьте команду `/sync` (когда будет реализовано)
2. Откройте Google таблицу
3. Данные должны появиться в таблице

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>Частые проблемы и решения</b></summary>

### Проблема: "ModuleNotFoundError: No module named 'app'"

**Решение:**
```bash
# Убедитесь что вы в корне проекта
cd EasyCamp-Teplo
# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема: "google.auth.exceptions.DefaultCredentialsError"

**Решение:**
- Проверьте что файл `google-credentials.json` существует
- Проверьте путь в `.env`: `GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json`

### Проблема: "TelegramConflictError: Conflict: terminated by other getUpdates"

**Решение:**
- Запущено несколько экземпляров бота
- Остановите все процессы Python:
  ```bash
  # Windows
  taskkill /F /IM python.exe
  
  # Linux/Mac
  pkill python
  ```

### Проблема: Бот не отвечает

**Решение:**
1. Проверьте что бот запущен (должно быть сообщение "Run polling for bot")
2. Проверьте токен в `.env`
3. Проверьте что вы админ (ваш Chat ID в `.env`)

</details>

---

## 📚 Дополнительные ресурсы

- [Документация Google Sheets API](https://developers.google.com/sheets/api)
- [Документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Документация Avito API](https://developers.avito.ru/)

---

## ✅ Контрольный список развертывания

- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Google Cloud Project настроен
- [ ] Service Account создан и ключ сохранен
- [ ] Google таблица создана и доступ предоставлен
- [ ] Telegram бот создан
- [ ] Файл `.env` заполнен
- [ ] Бот запущен и отвечает
- [ ] Тестовые данные созданы

---

**Время развертывания:** ~20-30 минут

**Последнее обновление:** 10.01.2026
