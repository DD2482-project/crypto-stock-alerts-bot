# Provisions the deployment host + minimal networking for the bot.
#
# Scope note: Terraform state is kept local (no remote backend configured).
# That's a deliberate simplification for a two-person, single-environment
# course project -- documented explicitly in the report rather than solved
# with a remote backend, per the brief's guidance to pick the simplest
# option and say so.

terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# SSH key used by the CD workflow's deploy step to reach the host.
resource "hcloud_ssh_key" "deploy" {
  name       = "crypto-stock-alerts-bot-deploy-key"
  public_key = var.ssh_public_key
}

# The bot has no inbound service: it long-polls Telegram and calls
# market-data APIs outbound only. SSH (for deployment) is therefore the
# only inbound rule this host needs.
resource "hcloud_firewall" "bot_host" {
  name = "crypto-stock-alerts-bot-fw"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = [var.ssh_allowed_cidr]
  }
}

resource "hcloud_server" "bot_host" {
  name         = "crypto-stock-alerts-bot"
  server_type  = var.server_type
  image        = "ubuntu-24.04"
  location     = var.location
  ssh_keys     = [hcloud_ssh_key.deploy.id]
  firewall_ids = [hcloud_firewall.bot_host.id]

  # Installs Docker + the Compose plugin and clones the repo (which
  # contains docker-compose.yml) so the CD workflow only ever has to SSH
  # in, write .env, and run `docker compose pull && up -d` -- it never
  # needs to bootstrap the host itself.
  user_data = <<-EOF2
    #cloud-init
    package_update: true
    packages:
      - ca-certificates
      - curl
      - git
    runcmd:
      - curl -fsSL https://get.docker.com | sh
      - systemctl enable --now docker
      - mkdir -p /opt/app
      - '[ -d /opt/app/.git ] || git clone https://github.com/${var.github_repository}.git /opt/app'
  EOF2
}
