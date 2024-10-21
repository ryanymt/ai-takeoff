variable "project_id" {
  type = string
  description = "The ID of the Google Cloud project"
}

variable "region" {
  type = string
  description = "The region for the Google Cloud project resources"
  default = "us-central1" # Set a default region
}

variable "billing_account" {
  type = string
  description = "The billing account ID for the Google Cloud project"
}
