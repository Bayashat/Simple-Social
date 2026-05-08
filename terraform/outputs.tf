output "render_service_url" {
  description = "Public HTTPS URL of the API. Use this as Streamlit Secret API_URL."
  value       = render_web_service.api.url
}

output "render_service_id" {
  description = "Render service id (for imports / support)."
  value       = render_web_service.api.id
}

output "supabase_project_ref" {
  description = "Supabase project ref (Session pooler user is postgres.<ref>)."
  value       = var.create_supabase_project ? supabase_project.main[0].id : null
}

output "database_url" {
  description = "Async DB URL wired into Render (sensitive)."
  value       = local.database_url_effective
  sensitive   = true
}

output "generated_secret_key" {
  description = "App SECRET_KEY generated in Terraform state (same value is set on Render)."
  value       = random_password.secret_key.result
  sensitive   = true
}
