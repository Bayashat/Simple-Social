variable "supabase_organization_id" {
  type        = string
  description = "Supabase organization slug (Dashboard → Organization settings)."
}

variable "supabase_project_name" {
  type        = string
  description = "Logical name for the new Supabase project."
  default     = "simple-social"
}

variable "supabase_region" {
  type        = string
  description = "Supabase project region (see https://supabase.com/docs/guides/platform/regions)."
  default     = "ap-southeast-1"
}

variable "supabase_pooler_host" {
  type        = string
  description = "Override Session pooler hostname. If null, uses a built-in map for known regions (aws-0-<region>.pooler.supabase.com)."
  default     = null
}

variable "create_supabase_project" {
  type        = bool
  description = "If false, skip supabase_project and set render DATABASE_URL from database_url."
  default     = true
}

variable "database_url" {
  type        = string
  sensitive   = true
  description = "Async SQLAlchemy URL for the API (postgresql+asyncpg://...). Required when create_supabase_project is false."
  default     = ""
}

variable "render_service_name" {
  type        = string
  description = "Render Web Service display name."
  default     = "Simple Social"
}

variable "render_plan" {
  type        = string
  description = "Render instance type. Use `free` if your workspace supports it; otherwise try `starter` (see Render dashboard / API errors)."
  default     = "free"
}

variable "render_region" {
  type        = string
  description = "One of: frankfurt, ohio, oregon, singapore, virginia."
  default     = "frankfurt"
}

variable "container_image_url" {
  type        = string
  description = "GHCR image repository (without tag), e.g. ghcr.io/bayashat/simple-social"
  default     = "ghcr.io/bayashat/simple-social"
}

variable "container_image_tag" {
  type        = string
  default     = "latest"
}

variable "ghcr_username" {
  type        = string
  description = "GitHub username for GHCR auth (for private images)."
  default     = ""
}

variable "ghcr_token" {
  type        = string
  sensitive   = true
  description = "GitHub PAT with read:packages if the image is private. Leave empty for public images."
  default     = ""
}

variable "imagekit_private_key" {
  type        = string
  sensitive   = true
  description = "Optional ImageKit private API key (omit for ImageKit-only uploads if not used)."
  default     = ""
}

variable "imagekit_url_endpoint" {
  type        = string
  description = "Optional IMAGEKIT_URL_ENDPOINT."
  default     = ""
}

variable "imagekit_upload_folder" {
  type        = string
  default     = "/posts"
}
