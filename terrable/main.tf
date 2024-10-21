terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"  # Use the latest version
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required services
resource "google_project_service" "services" {
  for_each = toset([
    "notebooks.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "aiplatform.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "dataflow.googleapis.com",
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com"
  ])

  project = var.project_id
  service = each.key
  disable_on_destroy = false
}

# Grant project owner role to users
resource "google_project_iam_member" "project_owners" {
  for_each = toset(var.project_owners)

  project = var.project_id
  role    = "roles/owner"
  member  = "user:${each.key}@example.com" # Replace with actual user emails
}
