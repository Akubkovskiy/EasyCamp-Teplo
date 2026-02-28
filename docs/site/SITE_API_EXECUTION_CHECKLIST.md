# Site+API Execution Checklist

## Этапы
- [x] E0 — Infra baseline + backup vpnbot config
- [x] E1 — Front/API/DB scaffold в отдельном docker-compose
- [ ] E2 — API models + migrations + booking request endpoint
- [ ] E3 — Front booking flow + форма заявки
- [ ] E4 — Безопасный reverse-proxy subdomain через vpnbot override
- [ ] E5 — Admin MVP
- [ ] E6 — Hardening
- [ ] E7 — UAT + launch

## Текущий статус
- Создан `site-stack/` (frontend/api/db)
- Локально поднято на loopback:
  - frontend: `127.0.0.1:3000`
  - api: `127.0.0.1:8001`
  - db: `127.0.0.1:5433`
- Сделан backup:
  - `/root/easycamp-bot/ops/vpnbot-baseline-20260228-134637`
