# crypto-stock-alerts-bot

A Telegram bot that lets users subscribe to price alerts for crypto and stock
symbols. A background scheduler polls market-data APIs and notifies users
when their target price or percentage-change threshold is met.

The bot itself is intentionally simple — the primary deliverable of this
project is the DevOps pipeline around it (CI, CD, Infrastructure as Code, and
quality/security automation). See `docs/report.md` for details.

## Repository layout

- `app/` — application source (Telegram handlers, scheduler, price sources,
  persistence, config, entrypoint)
- `tests/` — unit tests (pytest)
- `infra/terraform/` — infrastructure as code for the deployment host
- `.github/workflows/` — CI (`ci.yml`), CD (`cd.yml`), static analysis
  (`codeql.yml`)
- `docs/` — AI usage notes and final report

## Local development

```bash
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN etc.
pip install -r requirements.txt -r requirements-dev.txt
python -m app.main
```

## Team

- Jafar — Application & Continuous Integration
- Gabriel — Delivery, Infrastructure & Security
