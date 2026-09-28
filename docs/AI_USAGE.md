# AI Tool Usage

Each team member documents their own AI-assisted tool usage individually.

## Jafar

The CI pipeline, application code, and project structure were designed and
implemented by me; AI was used as a supporting tool during
that work. Specifically, it was used to:

- Fix errors encountered during development (e.g. debugging failing lint/test
  runs and issues found while wiring up the app and CI).
- Help understand unfamiliar configuration before applying it (e.g. GitHub
  Actions/ruleset options, Terraform variables) rather than changing settings
  blind.
- Generate and discuss ideas, which I then evaluated and adapted rather than
  applying as-is.

All AI-assisted changes were reviewed and verified against the actual
repository, CI results, and GitHub settings before being kept.

## Gabriel

The delivery pipeline, infrastructure and security automation are my half of the project. I used AI assistance  mainly for first drafts and unfamiliar configuration, then reviewed and tested everything myself. It was used to:

- Draft initial versions of the Dockerfile, docker-compose.yml, the Terraform configuration and the CD workflow, which I then ran and corrected against what the deployment actually needed.
- Explain configuration I had not used before (OCI networking, cloud-init, GitHub Actions outputs and secrets) instead of copying it blind.
- Help debug real CD failures diagnosed from the Actions logs: an unresolvable trivy-action version, an image tag rejected for uppercase letters in our organisation name, and a host checked out on the wrong branch
