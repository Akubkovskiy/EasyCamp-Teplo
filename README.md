# EasyCamp

[![CI](https://github.com/Akubkovskiy/EasyCamp-Teplo/actions/workflows/ci.yml/badge.svg)](https://github.com/Akubkovskiy/EasyCamp-Teplo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

**Open-source automation platform for small resorts and vacation rental businesses.**

> 🇷🇺 [Документация на русском](README.ru.md)

EasyCamp connects your **Telegram bot**, **Avito listings**, and **Google Sheets** into one automated management system — no paid SaaS required. Fork it, adapt it, run it on your own server.

**Battle-tested** on [Teplo resort](https://teplo-v-arkhyze.ru) (Arkhyz, Russia) since 2025.

---

## ✨ What it does

| Feature | Description |
|---------|-------------|
| 🤖 Telegram admin bot | Manage bookings, houses, staff — all from Telegram |
| 🔄 Avito sync | Auto-import bookings from Avito rental platform |
| 📊 Google Sheets | Real-time sync of all booking data |
| 🧹 Cleaning tasks | Assign and track cleaning staff via Telegram |
| 📅 Availability calendar | Interactive date picker for guests and staff |
| 🔔 Notifications | Instant alerts for new bookings and updates |

---

## 🚀 Quick Start

```bash
git clone https://github.com/Akubkovskiy/EasyCamp-Teplo.git
cd EasyCamp-Teplo
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
python -m uvicorn app.main:app --reload
```

Full setup guide (Google Sheets API, Telegram Bot, Avito): **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

---

## 🔧 Stack

- **Python 3.11** · FastAPI · aiogram 3.x
- **Database**: SQLite via SQLAlchemy (async)
- **Integrations**: Telegram Bot API · Avito API · Google Sheets API
- **Scheduler**: APScheduler for background sync
- **Deploy**: Docker Compose

---

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) — full self-hosting setup
- [Architecture](docs/architecture.md) — service structure and data flow
- [Roadmap](docs/roadmap.md) — planned features and MVP stages
- [Google Sheets Setup](docs/google_sheets_setup.md) — integration details

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The project is designed to be forked and adapted for any resort or vacation rental — PRs and feedback welcome.

## 📄 License

[MIT](LICENSE) © Alexey Kubkovskiy · [Telegram](https://t.me/Alexey_kubkovskiy)
