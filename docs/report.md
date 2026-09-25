# Crypto & Stock Alerts Telegram Bot: Final Report

## 1. Project and Architecture

We kept the application itself small on purpose: the point of this project is to demonstrate an integrated DevOps workflow, not to build a large system. What we built is a single-process Telegram bot that lets users create price alerts for cryptocurrencies and stocks. The repository holds the application, its tests, the container configuration, the CI/CD workflows, the Infrastructure as Code, and the project documentation, so the whole workflow lives in one GitHub repository.
We split the application into independent modules:

```
Telegram user
     │  /subscribe, /list, /unsubscribe
     ▼
app/bot.py ── price lookup ──▶ app/price_sources/
     │                           ├─ CoinGecko (crypto)
     │                           └─ Alpha Vantage (stocks)
     ▼
app/models.py ── SQLAlchemy / SQLite
     ▲
     │ active subscriptions
     │
app/scheduler.py
     │
     ▼
app/conditions.py ── trigger evaluation
     │
     └──────────────▶ Telegram notification
```

`app/main.py` is the composition root: it loads configuration, opens the database session factory, creates the Telegram application, registers the command handlers, and starts the scheduler. `app/bot.py` contains the Telegram commands. `app/models.py` provides persistence through SQLAlchemy and SQLite. `app/price_sources/` isolates the external market-data providers behind a common interface, while `app/conditions.py` contains pure trigger logic with no network or database dependency. `app/scheduler.py` periodically reads active subscriptions, obtains current prices, evaluates the conditions, sends notifications, and marks triggered subscriptions so the same alert is not repeatedly sent.
We chose this separation because it keeps external I/O at clear boundaries and makes the core logic easier to unit-test.

## 2. Development Platform and CI

We used GitHub as our development platform: source control, pull requests, branch rules, GitHub Actions, security results, and GitHub Container Registry (GHCR) all live there. We work on feature branches and integrate changes through pull requests into `main`.
The `main` branch is protected by an active ruleset. Direct integration into `main` requires a pull request, at least one approving review, and successful required CI status checks. The configured CI checks are `lint`, `test`, and `docker-build`. Force pushes and deletion of `main` are blocked and the bypass list is empty. This means a change cannot be merged simply because it compiles locally or because one person wrote it: it needs both a second pair of eyes and a passing automated gate.
The CI workflow (`.github/workflows/ci.yml`) runs on every push and pull request and contains four independent jobs:

- **`lint`** runs `ruff check .`. We picked Ruff because one tool covers common Python style, correctness, import-order, modernization, and bug-detection rules, instead of wiring up several separate linters.
- **`test`** runs `pytest --cov=app --cov-report=term-missing`. The tests cover the trigger logic, persistence layer, and price-source behavior. External HTTP calls are mocked so CI does not depend on third-party API availability or rate limits.
- **`docker-build`** builds the production Docker image. This catches broken Dockerfiles, missing dependencies, or packaging problems before a change can be merged.
- **`secret-scan`** runs Gitleaks against the checked-out repository to catch committed secrets (API keys, tokens, private keys) before they can reach `main`. It fails the job (rather than only logging a report) when it finds a match, so once added to the `main` ruleset's required checks it blocks the merge instead of just warning about it. `.gitleaks.toml` extends the default ruleset and allowlists `.env.example` by path, since its intentionally empty `KEY=` placeholders otherwise trip the generic-api-key rule as a false positive; every other file is still scanned against the full default rule set.

We also run CodeQL as an additional, security-focused workflow. It analyzes Python pull requests targeting `main` and also runs weekly on a schedule, looking for security-relevant code patterns that linting and unit tests don't catch.
Put together, the integration path looks like this:

```
feature branch → pull request → lint + tests + Docker build + CodeQL
              → one human approval → merge to protected main → CD
```

The branch rules turn CI from an advisory tool into an enforced quality gate.

## 3. Continuous Delivery and Containerization

Our CD workflow (`.github/workflows/cd.yml`) runs whenever changes reach `main`. Its first job builds the production Docker image and tags it with both the Git commit SHA and `latest`. The SHA tag gives us traceability between a deployed image and the exact source revision that produced it.
Before publishing the image, Trivy scans it for `HIGH` and `CRITICAL` vulnerabilities and uploads the SARIF result to GitHub's Security interface. We made the scan intentionally report-only (`exit-code: 0`): we chose visibility over automatically blocking every deployment, because an unpatched vulnerability in an upstream base image could otherwise stop all releases until someone else fixes it. That's a limitation we're stating on purpose rather than hiding; a stricter production system could block deployment for selected severity levels or approved vulnerability policies instead.
After scanning, the image is pushed to GHCR. The deployment job then connects to the provisioned host over SSH, creates the runtime `.env` file from GitHub Actions secrets, authenticates to GHCR using the workflow's short-lived `GITHUB_TOKEN`, pulls the image for the current commit, and starts it with Docker Compose. The workflow finishes with a smoke test that checks the bot container is running and that the configured Telegram token is accepted by Telegram's `getMe` endpoint.
The Dockerfile uses a two-stage build and runs the final application as a dedicated non-root user. Docker Compose publishes no inbound application ports, since the bot uses Telegram long-polling and only makes outbound connections. SQLite data lives on a named volume so subscriptions survive container replacement and redeployment.

## 4. Infrastructure as Code

We define the deployment infrastructure with Terraform under `infra/terraform/`. It provisions the Oracle Cloud Infrastructure (OCI) resources the application needs: a virtual cloud network, internet gateway, route table, security list, subnet, and compute instance. Cloud-init installs Docker, prepares `/opt/app`, and clones the repository so the host is ready for the CD workflow the moment it boots.
We chose OCI because its Always Free resources are enough for a small student workload at zero cost. The trade-off is more infrastructure work up front: networking resources that some VM providers create implicitly have to be declared explicitly in Terraform. That's more configuration than the bot itself strictly needs, but it makes the network and deployment environment reproducible, and it's a clearer demonstration of Infrastructure as Code than a one-click VM would have been.
The `VM.Standard.E2.1.Micro` shape we picked is x86_64, matching the Docker images the GitHub-hosted Ubuntu runners produce, so we didn't need to introduce multi-architecture image builds. Its CPU and memory are limited, which is fine for one lightweight polling process but wouldn't be enough for a larger service or a database server.
We keep Terraform state locally rather than in a remote backend. That's a reasonable simplification for a two-person, single-environment course project, though a team or production setup would normally use remote state with locking and controlled access.
One configuration detail has to stay consistent with the repository: the Terraform `github_repository` variable used by cloud-init must resolve to `DD2482-project/crypto-stock-alerts-bot`, not an older fork, or cloud-init clones the wrong repository on first boot.

## 5. Quality, Security, and AI-Assisted Tools

We integrated quality and security automation at several stages instead of treating it as a separate, manual activity. Ruff gives us static code-quality checks, pytest verifies application behavior, CodeQL performs static security analysis, the Docker build validates the deployable artifact, and Trivy scans that artifact before it's published. Dependabot (`.github/dependabot.yml`) opens weekly pull requests for outdated pip and GitHub Actions dependencies, so a known-vulnerable version doesn't just sit unnoticed in the repository. Secrets such as the Telegram token, API keys, deployment host, and SSH private key are supplied through GitHub Actions secrets rather than committed to the repository.
We also used AI-assisted tools during the project as development support: fixing errors we ran into during development, helping us understand unfamiliar configuration, and generating ideas to evaluate. We treated AI-generated suggestions as proposals rather than authoritative results: we checked configuration and code against the actual repository and GitHub settings ourselves, and the CI/CD workflows and tests remain the source of truth for whether the implementation works. Our use of AI-assisted tools is documented per team member in `docs/AI_USAGE.md`.

## 6. Limitations and Trade-offs

We think the result is a complete, working DevOps pipeline for what this course project asks for, not a partial one: every mandatory piece, CI, CD, Infrastructure as Code, a development platform with enforced branch rules, and several layers of quality and security automation, is implemented, wired together, and actually running in this repository, not just described in this report. What follows are the limitations and trade-offs we made along the way, and why we made them.

Several of these were scoping decisions, not oversights. The Trivy scan's report-only mode (§3) is one of them: we picked visibility over blocking every deploy on a CVE we can't fix ourselves. SSH is allowed from `0.0.0.0/0` because GitHub-hosted runners deploy from a large, changing IP range; the SSH key is still required to do anything, but a production setup should narrow this to a bastion, VPN, or self-hosted runner.

At the application level, SQLite has no replication or automated backup. That's acceptable for a single bot instance, but it's the first thing we'd change before running more than one. The in-process scheduler makes the same single-instance assumption: running two replicas would double-process the same subscriptions, since there's no distributed locking. The stock price source is also bounded by Alpha Vantage's free-tier rate limit, and crypto lookups currently rely on CoinGecko's internal coin ids rather than a friendlier ticker-resolution layer. Both are things we'd build out first if this were a real product instead of a course project.

We also caught and fixed a real issue while building this, not just a hypothetical one: the `secret-scan` job initially failed in CI on a false positive in `.env.example` (Gitleaks flagged the bare `STOCK_API_KEY=` placeholder as a possible secret). We fixed it with a scoped `.gitleaks.toml` allowlist for that one file rather than by weakening or disabling the check for everything else. It's a small example, but it shows the pipeline doing its job during development, not just existing on paper.

None of this touches the mandatory pieces: the pipeline described in sections 2 through 5 is fully wired together and running in this repository, not just documented in this report. Everything needed to reproduce it, the application code, tests, `Dockerfile`, `docker-compose.yml`, the CI/CD workflows, the Terraform configuration, and the setup instructions in `README.md`, is in this one place.