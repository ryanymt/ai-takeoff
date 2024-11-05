# enable APIs
resource "google_project_service" "services" {
  for_each = var.services
  service  = each.value

  project = var.project_id

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
  disable_on_destroy         = false
}

# add the project owners
resource "google_project_iam_binding" "owners" {
  for_each = toset(var.project_owners)

  project = var.project_id
  role    = "roles/owner"
  members = [
    "user:${each.key}"
  ]
}

module "cli" {
  source  = "terraform-google-modules/gcloud/google"
  version = "~> 3.0"

  platform              = "linux"
  additional_components = ["kubectl", "beta"]

  create_cmd_entrypoint = "${path.module}/scripts/persistent-resource.sh"
  create_cmd_body       = "create ${var.project_id} ${var.region}"

  destroy_cmd_entrypoint = "${path.module}/scripts/persistent-resource.sh"
  destroy_cmd_body       = "delete ${var.project_id} ${var.region}"
}
