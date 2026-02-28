# Teplo Site Stack (E0/E1 scaffold)

Безопасный старт сайта и API в отдельных контейнерах, без вмешательства в боевой VPN reverse-proxy.

## Что внутри
- `frontend` (Next.js dev, порт 3000 localhost)
- `api` (FastAPI dev, порт 8001 localhost)
- `db` (PostgreSQL, порт 5433 localhost)

## Важно
- Никаких изменений в `/root/vpnbot/config/location.conf`
- Внешние 80/443 не занимаем
- Проксирование на домен будет отдельным этапом через `override.conf`

## Быстрый старт
```bash
cd site-stack
cp .env.example .env
docker compose up -d
```

## Проверки
```bash
docker compose ps
curl -I http://127.0.0.1:3000 || true
curl -I http://127.0.0.1:8001/docs || true
```
