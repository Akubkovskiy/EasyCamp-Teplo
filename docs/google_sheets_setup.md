# Настройка Google Sheets API - Пошаговая инструкция

## Шаг 1: Создание Google Cloud Project

1. Перейдите на https://console.cloud.google.com/
2. Нажмите **"Select a project"** → **"New Project"**
3. Название проекта: `EasyCamp-Teplo`
4. Нажмите **"Create"**

## Шаг 2: Включение Google Sheets API

1. В меню слева выберите **"APIs & Services"** → **"Library"**
2. Найдите **"Google Sheets API"**
3. Нажмите **"Enable"**

## Шаг 3: Создание Service Account

1. Перейдите в **"APIs & Services"** → **"Credentials"**
2. Нажмите **"Create Credentials"** → **"Service Account"**
3. Заполните:
   - Service account name: `easycamp-sheets-bot`
   - Service account ID: `easycamp-sheets-bot` (автозаполнится)
   - Description: `Bot for syncing bookings with Google Sheets`
4. Нажмите **"Create and Continue"**
5. Role: выберите **"Editor"** (или можно пропустить)
6. Нажмите **"Done"**

## Шаг 4: Создание ключа

1. Найдите созданный Service Account в списке
2. Нажмите на него → вкладка **"Keys"**
3. Нажмите **"Add Key"** → **"Create new key"**
4. Выберите тип: **JSON**
5. Нажмите **"Create"**
6. **Файл скачается автоматически** (например, `easycamp-teplo-xxxxx.json`)

## Шаг 5: Сохранение ключа в проект

1. Переименуйте скачанный файл в `google-credentials.json`
2. Поместите его в корень проекта: `c:\projects\EasyCamp-Teplo\google-credentials.json`
3. **ВАЖНО:** Добавьте в `.gitignore`:
   ```
   google-credentials.json
   ```

## Шаг 6: Создание Google Таблицы

1. Откройте https://sheets.google.com/
2. Создайте новую таблицу
3. Название: **"EasyCamp Teplo - Брони"**
4. Скопируйте **ID таблицы** из URL:
   ```
   https://docs.google.com/spreadsheets/d/[ВОТ_ЭТОТ_ID]/edit
   ```

## Шаг 7: Предоставление доступа

1. В созданной таблице нажмите **"Share"** (Поделиться)
2. Вставьте email Service Account (из файла JSON, поле `client_email`)
   - Например: `easycamp-sheets-bot@easycamp-teplo.iam.gserviceaccount.com`
3. Права: **Editor**
4. Снимите галочку **"Notify people"**
5. Нажмите **"Share"**

## Шаг 8: Добавление переменных окружения

Добавьте в `.env`:
```env
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=ваш_id_таблицы_из_шага_6
```

## Готово!

После выполнения всех шагов сообщите мне, и я продолжу с установкой библиотек и написанием кода.

---

**Контрольный список:**
- [ ] Google Cloud Project создан
- [ ] Google Sheets API включен
- [ ] Service Account создан
- [ ] JSON ключ скачан и сохранен
- [ ] Таблица создана
- [ ] Доступ предоставлен Service Account
- [ ] Переменные добавлены в .env
