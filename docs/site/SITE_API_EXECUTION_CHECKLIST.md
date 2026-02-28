# Site+API Execution Checklist

## Этапы
- [x] E0 — Infra baseline + backup vpnbot config
- [x] E1 — Front/API/DB scaffold в отдельном docker-compose
- [x] E2 — API models + booking request endpoint (MVP)
- [x] T-plan — Testing stack roadmap создан
- [x] E3 — Front booking flow + форма заявки (MVP)
- [x] T1 — API smoke (manual curl) выполнен
- [x] T2 (часть) — UI smoke (frontend доступен + отправка заявки через API)
- [~] E4 — Безопасный reverse-proxy subdomain через vpnbot override (template+rollback готовы)
- [ ] E5 — Admin MVP
- [ ] E6 — Hardening
- [ ] E7 — UAT + launch

## Текущий статус
- Создан `site-stack/` (frontend/api/db)
- API (MVP) реализован:
  - `GET /health`
  - `GET /houses`
  - `POST /booking-requests`
  - `GET /booking-requests/{id}`
- Локально поднято на loopback:
  - frontend: `127.0.0.1:3000`
  - api: `127.0.0.1:8001`
  - db: `127.0.0.1:5433`
- Сделан backup:
  - `/root/easycamp-bot/ops/vpnbot-baseline-20260228-134637`
