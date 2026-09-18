# Input variables for host + networking provisioning.
#
# Provider choice: Hetzner Cloud (hcloud). Chosen over AWS/GCP/Azure/
# DigitalOcean because it needs no ID verification for cheap instances,
# has a small/simple Terraform provider, and its cheapest server type
# (cx22) is more than enough for a single polling bot -- explicitly noted
# as the "simplest option satisfying the DoD" per the brief.

variable "hcloud_token" {
  description = "Hetzner Cloud API token. Set via TF_VAR_hcloud_token env var or a git-ignored *.auto.tfvars file -- never commit it."
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "Public half of the deploy SSH key installed on the host. The matching private key is stored as the DEPLOY_SSH_KEY GitHub Actions secret and used by the CD workflow to deploy."
  type        = string
}

variable "server_type" {
  description = "Hetzner Cloud server type. cx22 (2 vCPU / 4GB) is the cheapest current shared-vCPU type and is oversized for this workload, but it's the simplest available option."
  type        = string
  default     = "cx22"
}

variable "location" {
  description = "Hetzner Cloud datacenter location."
  type        = string
  default     = "nbg1"
}

variable "ssh_allowed_cidr" {
  description = "CIDR range allowed to reach the host on port 22. Left open (0.0.0.0/0) by default for course-project simplicity; narrow this to the deploy runner's IP or a personal IP in a real deployment (documented as a trade-off in the report)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "github_repository" {
  description = "owner/repo of this project on GitHub. Used by cloud-init to git-clone the repo (for docker-compose.yml and .env template) onto the host at first boot. The repo is assumed public; a private repo would need a deploy token added to the clone URL."
  type        = string
  default     = "sund02/crypto-stock-alerts-bot"
}
