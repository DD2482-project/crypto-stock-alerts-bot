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
- `.github/PULL_REQUEST_TEMPLATE.md` — required PR checklist
- `.gitleaks.toml` — secret-scanning config for the `secret-scan` CI job
- `Dockerfile`, `docker-compose.yml` — container build and runtime config
- `docs/` — AI usage notes and final report

## Bot commands

- `/start`, `/help` — usage summary
- `/subscribe <symbol> <price|pct> <value>` — create an alert, e.g.
  `/subscribe bitcoin price 70000` or `/subscribe AAPL pct -5`. Asset type
  (crypto vs. stock) is inferred: the symbol is first looked up as a
  CoinGecko coin id, falling back to a stock ticker.
- `/list` — show your subscriptions and their status
- `/unsubscribe <id>` — remove a subscription by its id

## Configuration

Copy `.env.example` to `.env` and fill in real values:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | Token from [@BotFather](https://t.me/BotFather) |
| `CRYPTO_API_KEY` | no | CoinGecko demo API key; the free tier works without one |
| `STOCK_API_KEY` | only for stock subscriptions | Alpha Vantage API key |
| `POLL_INTERVAL_SECONDS` | no (default `60`) | How often the scheduler checks prices |
| `DATABASE_PATH` | no (default `alerts.db`) | SQLite file path |

Never commit `.env`; only `.env.example` (with empty placeholder values) is
tracked in the repository.

## Local development

```bash
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN etc.
pip install -r requirements.txt -r requirements-dev.txt
python -m app.main
```

Run the checks the CI pipeline runs before opening a PR:

```bash
ruff check .
pytest --cov=app --cov-report=term-missing
docker build -t crypto-stock-alerts-bot:ci .
```

## Running with Docker

```bash
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN etc.
docker compose up --build
```

SQLite data persists in the `bot_data` named volume across restarts and
rebuilds.

## Contributing

`main` is protected: changes land through a pull request that needs one
approving review and passing `lint`/`test`/`docker-build` status checks (see
`.github/PULL_REQUEST_TEMPLATE.md` for the PR checklist). `secret-scan` also
runs on every PR and fails on a detected secret; add it to the ruleset's
required checks once GitHub has seen it run. Force-pushes and deletions of
`main` are blocked.

## Deployment

Merges to `main` trigger the CD workflow (`.github/workflows/cd.yml`), which
builds and scans the Docker image, pushes it to GHCR, and deploys it over
SSH to the Terraform-provisioned host. See `docs/report.md` for the full
CI/CD and infrastructure design, and `infra/terraform/` for the OCI setup.

**Note for graders:** the live host runs on an Oracle Cloud (OCI) trial
account, which is time-limited (roughly 20–30 days). If the deployed bot or
a `terraform plan`/`apply` against it no longer works by the time this is
reviewed, that's the trial expiring, not a bug in the pipeline itself. The
CI/CD workflows, tests, and Terraform config remain fully runnable against
a fresh OCI account.

## Team

- Jafar — Application & Continuous Integration, including the `main` branch
  ruleset (required PR + 1 approving review + required `lint`/`test`/`docker-build`
  status checks, no force-push/delete) that turns CI into an enforced merge gate.
  Also wrote `docs/report.md`, covering both members' work.
- Gabriel — Delivery, Infrastructure & Security
