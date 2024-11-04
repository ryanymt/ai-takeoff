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
