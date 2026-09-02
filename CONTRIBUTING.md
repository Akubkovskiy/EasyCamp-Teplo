# Contributing to EasyCamp

Thank you for your interest in contributing to EasyCamp! This project aims to be a reusable open-source platform for resort and camp management automation.

## Ways to Contribute

- **Bug reports** — open an Issue with steps to reproduce
- **Feature requests** — describe the use case and expected behavior
- **Code contributions** — see the guide below
- **Documentation** — improve README, add examples, translate to other languages

## Development Setup

```bash
git clone https://github.com/Akubkovskiy/EasyCamp-Teplo.git
cd EasyCamp-Teplo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env  # fill in your test credentials
```

## Reproducible Tests

Use Python 3.11 in a fresh environment. Do not run the suite with a global
FastAPI/Starlette installation, and do not place a production `.env`, database
or credentials in a clean test checkout. The CI guard verifies the supported
runtime before pytest starts.

PowerShell example with synthetic values:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
$env:PYTHONUTF8 = "1"
$env:TELEGRAM_BOT_TOKEN = "0000000000:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TELEGRAM_CHAT_ID = "123456789"
$env:SITE_LEAD_TOKEN = "test-token"
$env:DATABASE_URL = "sqlite+aiosqlite:///./test.db"
.\.venv\Scripts\python.exe -m pytest -q
```

The same command is used in CI with Python 3.11. The checked-in dependency
range resolves FastAPI `<0.115` and Starlette `<0.39`; an incompatible global
environment is not a valid verification result.

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

We use **ruff** for linting:
```bash
ruff check app/
ruff format app/
```

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/your-feature`
2. Make your changes with tests
3. Ensure CI passes (lint + tests + security)
4. Open a PR with a clear description of what and why

## Adapting for Your Resort

EasyCamp is designed to be forked and customized. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full setup guide.

If you adapt it for a new use case, consider opening a PR or linking back — it helps the community grow.

## License

By contributing, you agree your contributions will be licensed under the [MIT License](LICENSE).
