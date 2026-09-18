# Provisions the deployment host + networking for the bot on Oracle Cloud
# Infrastructure (Always Free tier).
#
# Scope note: Terraform state is kept local (no remote backend configured).
# That is a deliberate simplification for a two-person, single-environment
# course project, documented rather than solved with a remote backend.
#
# Unlike single-VM providers, OCI has no implicit default network, so the
# full path from instance to internet is declared here:
#   VCN -> internet gateway -> route table -> subnet -> instance
# with a security list controlling what may cross the subnet boundary.

terraform {
  required_version = ">= 1.5"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Availability domains vary per tenancy and region; take the first one
# rather than hardcoding a name that would not exist elsewhere.
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Resolve the newest Ubuntu 24.04 image that supports the chosen shape,
# so the config does not pin an image OCID that Oracle will eventually
# retire.
data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# ---------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------

resource "oci_core_vcn" "bot" {
  compartment_id = var.compartment_ocid
  display_name   = "crypto-stock-alerts-bot-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "botvcn"
}

# The bot needs outbound internet access (Telegram long-polling, the
# market-data APIs, and pulling its image from GHCR), which requires an
# internet gateway even though nothing inbound but SSH is allowed.
resource "oci_core_internet_gateway" "bot" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.bot.id
  display_name   = "crypto-stock-alerts-bot-igw"
  enabled        = true
}

resource "oci_core_route_table" "bot" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.bot.id
  display_name   = "crypto-stock-alerts-bot-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.bot.id
  }
}

resource "oci_core_security_list" "bot" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.bot.id
  display_name   = "crypto-stock-alerts-bot-sl"

  # All outbound traffic: needed for Telegram, market-data APIs and GHCR.
  egress_security_rules {
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol         = "all"
  }

  # SSH is the only inbound rule. The bot exposes no service of its own:
  # it long-polls Telegram rather than receiving webhooks, so no other
  # port needs to be reachable.
  ingress_security_rules {
    source      = var.ssh_allowed_cidr
    source_type = "CIDR_BLOCK"
    protocol    = "6" # TCP

    tcp_options {
      min = 22
      max = 22
    }
  }
}

resource "oci_core_subnet" "bot" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.bot.id
  display_name      = "crypto-stock-alerts-bot-subnet"
  cidr_block        = "10.0.1.0/24"
  route_table_id    = oci_core_route_table.bot.id
  security_list_ids = [oci_core_security_list.bot.id]
  dns_label         = "botsubnet"
}

# ---------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------

resource "oci_core_instance" "bot" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "crypto-stock-alerts-bot"
  shape               = var.instance_shape

  create_vnic_details {
    subnet_id        = oci_core_subnet.bot.id
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key

    # Installs Docker and clones the repo (which carries
    # docker-compose.yml) so the CD workflow only has to SSH in, write
    # .env, and run `docker compose pull && up -d`.
    #
    # Oracle's Ubuntu images log in as the `ubuntu` user, not root, so the
    # user is added to the docker group and given ownership of /opt/app --
    # otherwise every deploy command would need sudo.
    user_data = base64encode(<<-CLOUDINIT
      #cloud-config
      package_update: true
      packages:
        - ca-certificates
        - curl
        - git
      runcmd:
        - curl -fsSL https://get.docker.com | sh
        - systemctl enable --now docker
        - usermod -aG docker ubuntu
        - mkdir -p /opt/app
        - '[ -d /opt/app/.git ] || git clone https://github.com/${var.github_repository}.git /opt/app'
        - chown -R ubuntu:ubuntu /opt/app
      CLOUDINIT
    )
  }
}
