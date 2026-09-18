# Outputs consumed manually when wiring GitHub Actions secrets for the CD
# workflow (terraform apply is run out-of-band from CI in this project's
# scope -- see report for the trade-off).

output "server_ipv4" {
  description = "Public IPv4 address of the deployment host. Set this as the DEPLOY_HOST GitHub Actions secret."
  value       = oci_core_instance.bot.public_ip
}

output "deploy_user" {
  description = "Login user for the host. Oracle's Ubuntu images use `ubuntu`, not root. Set this as the DEPLOY_USER GitHub Actions secret."
  value       = "ubuntu"
}

output "instance_ocid" {
  description = "OCID of the compute instance, for reference in the OCI console."
  value       = oci_core_instance.bot.id
}
