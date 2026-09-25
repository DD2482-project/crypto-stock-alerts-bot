# Input variables for host + networking provisioning.
#
# Provider choice: Oracle Cloud Infrastructure (OCI). Chosen because its
# "Always Free" tier covers this workload permanently at no cost, which
# suits a student project with no billing budget. Trade-off: OCI requires
# considerably more explicit infrastructure than a single-VM provider --
# a VCN, internet gateway, route table, security list and subnet all have
# to be declared before an instance can exist. That verbosity is itself a
# useful demonstration of Infrastructure as Code, but it is more moving
# parts than this bot strictly needs.
#
# Shape choice: VM.Standard.E2.1.Micro (AMD, x86_64) rather than the
# larger VM.Standard.A1.Flex (Arm). Two reasons:
#   1. Architecture. Our CD pipeline builds the Docker image on GitHub's
#      ubuntu-latest runners, which are x86_64. An Arm host could not run
#      that image without adding cross-platform builds (QEMU/buildx) to
#      the pipeline.
#   2. Availability. A1.Flex capacity in free tenancies is frequently
#      exhausted ("Out of host capacity"), whereas E2.1.Micro is far more
#      reliably obtainable.
# The cost is that E2.1.Micro is small (1/8 OCPU, 1 GB RAM) -- fine for a
# single polling process, but it could not host a database or a build.

# ---------------------------------------------------------------------
# OCI API authentication.
# All five come from the config snippet OCI shows when you add an API key
# under Profile -> My profile -> API keys. None may be committed.
# ---------------------------------------------------------------------

variable "tenancy_ocid" {
  description = "OCID of the tenancy (root of the account)."
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user whose API key signs Terraform's requests."
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the uploaded API signing key."
  type        = string
}

variable "private_key_path" {
  description = "Local path to the API signing private key (.pem) downloaded when the API key was created. The file itself must stay outside the repo."
  type        = string
}

variable "region" {
  description = "OCI region identifier, e.g. eu-stockholm-1 or eu-frankfurt-1. Must be the tenancy's home region for Always Free resources."
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment to create resources in. The tenancy OCID itself works as the root compartment."
  type        = string
}

# ---------------------------------------------------------------------
# Host configuration.
# ---------------------------------------------------------------------

variable "ssh_public_key" {
  description = "Public half of the deploy SSH key installed on the host. The matching private key is stored as the DEPLOY_SSH_KEY GitHub Actions secret and used by the CD workflow to deploy."
  type        = string
}

variable "instance_shape" {
  description = "Compute shape. VM.Standard.E2.1.Micro is Always Free eligible and x86_64, matching the images our CD pipeline builds."
  type        = string
  default     = "VM.Standard.E2.1.Micro"
}

variable "ssh_allowed_cidr" {
  description = "CIDR range allowed to reach the host on port 22. Left open (0.0.0.0/0) for course-project simplicity, because GitHub-hosted runners deploy from a large and changing IP range; a production deployment should narrow this to a bastion or VPN range."
  type        = string
  default     = "0.0.0.0/0"
}

variable "github_repository" {
  description = "owner/repo of this project on GitHub. Used by cloud-init to git-clone the repo (for docker-compose.yml) onto the host at first boot. The repo is assumed public; a private repo would need a deploy token in the clone URL."
  type        = string
  default     = "DD2482-project/crypto-stock-alerts-bot"
}
