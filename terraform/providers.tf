# Credentials (do not commit secrets):
# - Supabase: SUPABASE_ACCESS_TOKEN (https://supabase.com/dashboard/account/tokens)
# - Render:   RENDER_API_KEY, RENDER_OWNER_ID (user/team settings URL in dashboard)

provider "supabase" {}

provider "render" {}

provider "random" {}
