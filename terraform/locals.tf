locals {
  # Session pooler hostname pattern (Supabase AWS). Override with var.supabase_pooler_host if needed.
  supabase_pooler_host_by_region = {
    "ap-southeast-1" = "aws-0-ap-southeast-1.pooler.supabase.com"
    "ap-southeast-2" = "aws-0-ap-southeast-2.pooler.supabase.com"
    "ap-northeast-1" = "aws-0-ap-northeast-1.pooler.supabase.com"
    "ap-northeast-2" = "aws-0-ap-northeast-2.pooler.supabase.com"
    "ap-south-1"     = "aws-0-ap-south-1.pooler.supabase.com"
    "eu-central-1"   = "aws-0-eu-central-1.pooler.supabase.com"
    "eu-west-1"      = "aws-0-eu-west-1.pooler.supabase.com"
    "eu-west-2"      = "aws-0-eu-west-2.pooler.supabase.com"
    "us-east-1"      = "aws-0-us-east-1.pooler.supabase.com"
    "us-west-1"      = "aws-0-us-west-1.pooler.supabase.com"
  }

  supabase_pooler_host = coalesce(
    var.supabase_pooler_host,
    try(local.supabase_pooler_host_by_region[var.supabase_region], null)
  )

  # Conditional branch avoids indexing supabase when create_supabase_project is false (short-circuit).
  database_url_effective = var.create_supabase_project ? format(
    "postgresql+asyncpg://postgres.%s:%s@%s:5432/postgres?sslmode=require",
    supabase_project.main[0].id,
    urlencode(random_password.supabase_database[0].result),
    local.supabase_pooler_host
  ) : var.database_url
}
