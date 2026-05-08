resource "random_password" "supabase_database" {
  count = var.create_supabase_project ? 1 : 0

  length  = 24
  special = true
}

resource "supabase_project" "main" {
  count = var.create_supabase_project ? 1 : 0

  organization_id         = var.supabase_organization_id
  name                    = var.supabase_project_name
  region                  = var.supabase_region
  database_password       = random_password.supabase_database[0].result
  instance_size           = "micro"
  legacy_api_keys_enabled = false

  timeouts {
    create = "45m"
    update = "45m"
  }

  lifecycle {
    precondition {
      condition     = local.supabase_pooler_host != null || !var.create_supabase_project
      error_message = "Unknown supabase_region for pooler host. Set supabase_pooler_host explicitly."
    }
  }
}
