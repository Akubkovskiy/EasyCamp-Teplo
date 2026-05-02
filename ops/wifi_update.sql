-- WiFi credentials update for EasyCamp houses
-- Run on FI:
--   docker exec easycamp_bot sqlite3 /app/data/easycamp.db < /root/easycamp-bot/ops/wifi_update.sql
--
-- Or interactively:
--   docker exec -it easycamp_bot sqlite3 /app/data/easycamp.db
--   .tables
--   SELECT id, name FROM houses;
--   (then copy the UPDATE statements below)

-- House 1: Домик в лесу 34м²
UPDATE houses
SET wifi_info = 'Сеть: Tenda
Пароль: 21102016'
WHERE name LIKE '%лесу%' OR name LIKE '%34%';

-- House 2: Домик семейный 40м²
UPDATE houses
SET wifi_info = 'Сеть: Tenda
Пароль: 21102016'
WHERE name LIKE '%семей%' OR name LIKE '%40%';

-- House 3: Компактный домик 32м²
-- Основная сеть
UPDATE houses
SET wifi_info = 'Сеть: Teplo
Пароль: tutTeplo

Резервная сеть: Tenda_ext
Пароль: 21102016'
WHERE name LIKE '%омпакт%' OR name LIKE '%32%';

-- Verify
SELECT id, name, wifi_info FROM houses;
