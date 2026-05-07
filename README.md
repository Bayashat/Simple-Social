# 📸 Simple Social

[ 🇬🇧 English ](README.md) | [ 🇰🇿 Қазақша ](docs/README_KK.md) | [ 🇷🇺 Русский ](docs/README_RU.md)

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![uv](https://img.shields.io/badge/uv-managed-purple.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688.svg?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-389776.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B.svg?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Local_DB-003B57.svg?logo=sqlite&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-Async_ORM-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/fastapi--users-JWT-black.svg)
![ImageKit](https://img.shields.io/badge/ImageKit-Media_CDN-000000.svg)
![AWS_S3](https://img.shields.io/badge/AWS-S3_FF9900.svg?logo=amazons3&logoColor=white)
![Boto3](https://img.shields.io/badge/boto3-SDK-232F3E.svg?logo=amazon-aws&logoColor=white)

A lightweight social-style app: **FastAPI** REST API plus a **Streamlit** web UI. Users register, upload media, and browse a feed.

> **Dual object storage:** the backend and UI **both support ImageKit *and* AWS S3.** Each upload selects one target (**ImageKit** for CDN + server-side transforms, **S3** for your own bucket via `boto3`). ImageKit URLs can use transformation chains in the feed; raw S3 URLs are shown unchanged.

## 🚀 Features

- **Authentication:** Registration & login via JWT (`fastapi-users`).
- **Media uploads:** Images, videos, and generic files (PDF, HTML, …) per backend MIME classification.
- **Dual storage (required product feature):** every share can go to **ImageKit** *or* **AWS S3** — configure both in `.env`, pick in the UI before **Share**.
- **Feed:** Sorted posts with owner-aware delete; each card shows **Storage: ImageKit** or **Storage: AWS S3**.
- **ImageKit-only UI transforms:** Caption overlays (URL-based) apply only when `storage=imagekit`.

## 📷 Screenshots

| Upload (storage picker) | Feed (posts + storage labels) |
|:--:|:--:|
| ![Upload page](docs/images/upload_page.png) | ![Feed page](docs/images/feed_page.png) |

## ⚙️ Setup

1. Clone the repo and `cd` into the project root.
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Create `.env` file based on `.env.example`.

## 🏃 How to run

Use **two terminals** (backend + frontend).

**Backend —** `http://localhost:8000` (Swagger: `/docs`)

```bash
uv run uvicorn app.main:app --reload
```

**Frontend —** `http://localhost:8501`

```bash
uv run streamlit run frontend/app.py
```

Run Streamlit from the **repo root** so imports and paths match; optional `frontend/.streamlit/config.toml` controls upload size hints.

## 📁 Project layout

```text
.
├── app/                 # FastAPI app
│   ├── main.py
│   ├── lifespan.py
│   ├── db.py
│   ├── dependencies.py
│   ├── models/
│   ├── routers/         # auth, users, posts
│   ├── schemas/
│   ├── services/
│   ├── images.py        # ImageKit client
│   ├── s3_storage.py    # S3 uploads / deletes
│   └── users.py         # FastAPI Users wiring
├── docs/                # Localized READMEs + screenshots
│   ├── README_KK.md
│   ├── README_RU.md
│   └── images/          # UI screenshots for documentation
├── frontend/
│   ├── app.py           # Streamlit UI
│   └── .streamlit/
├── pyproject.toml
├── uv.lock
└── .env                 # local secrets
```
