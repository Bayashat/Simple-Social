# Terraform: Supabase + Render

This stack creates (or optionally wires):

- **Supabase** — a `supabase_project` (Alpha provider) sized `micro`, with a **Session pooler** connection string wired to Render (`postgres.<project_ref>@…pooler.supabase.com:5432`).
- **Render** — one **Web Service** from your **GHCR** image (same convention as [.github/workflows/cd.yml](../.github/workflows/cd.yml): `ghcr.io/bayashat/simple-social:latest`).

**Streamlit Community Cloud** is not managed by Terraform: configure it manually (secrets below).

## Prerequisites

| Item | Notes |
|------|--------|
| [Terraform](https://developer.hashicorp.com/terraform/install) | `>= 1.5` |
| Supabase token | Dashboard → Account → Access tokens → `SUPABASE_ACCESS_TOKEN` |
| Org slug | Dashboard URL / org settings → `supabase_organization_id` |
| Render API key | User settings → API keys → `RENDER_API_KEY` |
| Render owner id | Individual `usr-…` or team `tea-…` → `RENDER_OWNER_ID` |
| GHCR visibility | Public image: omit `ghcr_*` variables. Private: GitHub PAT with `read:packages` |

Do **not** commit `terraform.tfvars` or `.env`; use [.env.example](../.env.example) locally for app dev only.

## Quick start

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # edit values
export SUPABASE_ACCESS_TOKEN=…
export RENDER_API_KEY=…
export RENDER_OWNER_ID=…
terraform init
terraform plan
terraform apply
```

Save the **`render_service_url`** output for Streamlit (`API_URL`). The first Supabase provisioning can take **many minutes**.

## Variables (summary)

- **`create_supabase_project`** — Default `true`. Set `false` and populate **`database_url`** with your existing pooled **asyncpg** URL if the Supabase provider is unavailable or you prefer a manual DB.
- **`supabase_region`** — Must match Asia-Pacific selection (default `ap-southeast-1`). If the Session pooler host differs from the built-in map, set **`supabase_pooler_host`** explicitly.
- **`render_plan`** — Default `free`. If Render API rejects `free`, set `starter` (or the plan string shown on the dashboard) in `terraform.tfvars`.
- **Image** — `container_image_url` + `container_image_tag` default to `ghcr.io/bayashat/simple-social` / `latest`.
- **S3** — Intentionally **not** set here (aligned with skipping S3 in production). Optional ImageKit vars are supported if you upload via ImageKit.

## Render environment

The Web Service receives at least:

- `SECRET_KEY` — generated (`random_password`) and stored only in Terraform state + Render UI.
- `DATABASE_URL` — built from Supabase Session pooler (or your `database_url` override).
- `IMAGEKIT_UPLOAD_FOLDER` — `/posts` by default; add ImageKit secrets if you enable uploads.

The container **[Dockerfile](../Dockerfile)** already runs `alembic upgrade head` before `uvicorn`, so the schema reaches `head` on each deploy without extra Render env vars.

## Streamlit Community Cloud

This repo uses [`frontend/app.py`](../frontend/app.py), which reads:

```text
API_URL = os.getenv("API_URL", "http://localhost:8000")
```

In **App settings → Secrets**, set:

```toml
API_URL = "https://YOUR-RENDER-SERVICE.onrender.com"
```

Use the **`render_service_url`** output from Terraform (no trailing slash). Redeploy the Streamlit app after changing URLs.

Python version (`3.13`) and entrypoint `frontend/app.py` remain your Streamlit Cloud settings (mirror local `uv run streamlit run frontend/app.py` from repo root).

## CI/CD with GitHub Actions

[Merging to `main`](../.github/workflows/cd.yml) builds and pushes a new `:latest` image and calls **`RENDER_DEPLOY_HOOK_URL`** (if set). Terraform-managed Render services **reload** after you either:

1. Invoke the dashboard **Deploy**, or
2. Run `curl -X POST "$RENDER_DEPLOY_HOOK_URL"` (same hook as Actions),

so you do **not** need `terraform apply` for every image digest change unless you also change infra.

## Fallback: manual Supabase project

If `terraform apply` fails on `supabase_project` (billing, quotas, Alpha API):

1. Set `create_supabase_project = false` in `terraform.tfvars`.
2. Paste **`database_url`** = Session pooler string from Supabase, converted for the app (`postgresql` + `postgresql+asyncpg://…` scheme; see [app/core/config.py](../app/core/config.py)).
3. `terraform apply` again — only Render (and GHCR credential if needed) updates.

Do not paste passwords into issues or Slack.

## State and lock file

Commit **`.terraform.lock.hcl`** after `terraform init` so CI/teammates resolve the same provider versions. Keep **`terraform.tfstate`** private (local backend by default).

## Sensitive outputs

- `database_url`, `generated_secret_key` — `terraform output -json` respects `sensitive = true`; avoid logging these in pipelines.
