resource "render_registry_credential" "ghcr" {
  count = var.ghcr_token != "" ? 1 : 0

  name       = "${var.render_service_name} GHCR"
  registry   = "GITHUB"
  username   = var.ghcr_username
  auth_token = var.ghcr_token
}

resource "render_web_service" "api" {
  name              = var.render_service_name
  plan              = var.render_plan
  region            = var.render_region
  health_check_path = "/docs"

  runtime_source = {
    image = merge(
      {
        image_url = var.container_image_url
        tag       = var.container_image_tag
      },
      length(render_registry_credential.ghcr) > 0 ? {
        registry_credential_id = render_registry_credential.ghcr[0].id
      } : {}
    )
  }

  env_vars = merge(
    {
      SECRET_KEY             = { value = random_password.secret_key.result }
      DATABASE_URL           = { value = local.database_url_effective }
      IMAGEKIT_UPLOAD_FOLDER = { value = var.imagekit_upload_folder }
    },
    var.imagekit_private_key != "" ? { IMAGEKIT_PRIVATE_KEY = { value = var.imagekit_private_key } } : {},
    var.imagekit_url_endpoint != "" ? { IMAGEKIT_URL_ENDPOINT = { value = var.imagekit_url_endpoint } } : {},
  )

  lifecycle {
    precondition {
      condition     = var.create_supabase_project || trimspace(var.database_url) != ""
      error_message = "When create_supabase_project is false, set database_url (non-empty async Postgres URL)."
    }
  }
}
