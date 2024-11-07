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
  create_cmd_body       = "create ${var.project_id} ${var.region} ${var.resource_id}"

  destroy_cmd_entrypoint = "${path.module}/scripts/persistent-resource.sh"
  destroy_cmd_body       = "delete ${var.project_id} ${var.region} ${var.resource_id}"

  depends_on = [google_project_service.services]
}

# BQ reservations
resource "google_bigquery_reservation" "reservation" {
  name     = var.resource_id
  location = var.region

  // Set to 0 for testing purposes
  // In reality this would be larger than zero
  slot_capacity     = 100
  edition           = "ENTERPRISE"
  ignore_idle_slots = true
  concurrency       = 0
  autoscale {
    max_slots = 100
  }
}
