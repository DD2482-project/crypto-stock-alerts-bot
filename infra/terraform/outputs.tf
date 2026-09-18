# Outputs consumed manually when wiring GitHub Actions secrets for the CD
# workflow (Terraform apply is run out-of-band from CI in this project's
# scope -- see report for the trade-off).

output "server_ipv4" {
  description = "Public IPv4 address of the deployment host. Set this as the DEPLOY_HOST GitHub Actions secret."
  value       = hcloud_server.bot_host.ipv4_address
}

output "ssh_key_id" {
  description = "Hetzner Cloud ID of the SSH key installed on the host."
  value       = hcloud_ssh_key.deploy.id
}
