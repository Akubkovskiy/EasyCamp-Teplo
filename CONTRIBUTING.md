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
