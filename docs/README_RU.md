# 📸 Simple Social

[ 🇬🇧 English ](../README.md) | [ 🇰🇿 Қазақша ](README_KK.md) | [ 🇷🇺 Русский ](README_RU.md)

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![uv](https://img.shields.io/badge/uv-управление-purple.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688.svg?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-389776.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B.svg?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-БД_локально-003B57.svg?logo=sqlite&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-Async_ORM-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/fastapi--users-JWT-black.svg)
![ImageKit](https://img.shields.io/badge/ImageKit-Media_CDN-000000.svg)
![AWS_S3](https://img.shields.io/badge/AWS-S3_FF9900.svg?logo=amazons3&logoColor=white)
![Boto3](https://img.shields.io/badge/boto3-SDK-232F3E.svg?logo=amazon-aws&logoColor=white)

Небольшое приложение в духе соцсети: REST API на **FastAPI** и веб‑интерфейс на **Streamlit**.

> **Два хранилища с полной поддержкой:** бэкенд и интерфейс работают **и с ImageKit, и с AWS S3.** При каждой загрузке выбирается одна цель (**ImageKit** — CDN и трансформации; **S3** — ваш бакет через `boto3`). На ленте для ImageKit применяются URL‑трансформации; ссылки S3 показываются как есть.

## 🚀 Возможности

- **Аутентификация:** регистрация и вход через JWT (`fastapi-users`).
- **Загрузка медиа:** изображения, видео и произвольные файлы (например PDF, HTML) по классификации MIME на бэкенде.
- **Два объектных хранилища:** **ImageKit или AWS S3** — укажите оба в `.env`, выбор в UI перед **Share** (`boto3`).
- **Лента:** посты по времени; автор удаляет свои; в шапке карточки — **Storage: ImageKit** или **Storage: AWS S3**.
- **Трансформации:** только для `storage=imagekit`.

## 📷 Скриншоты

### Страница загрузки (выбор хранилища)

![Загрузка — выбор ImageKit или AWS S3](./images/upload_page.png)

### Лента (публикации и подпись Storage)

![Лента — посты с метками ImageKit / AWS S3](./images/feed_page.png)

## ⚙️ Настройка

1. Клонируйте репозиторий и перейдите в корень проекта.
2. Установите зависимости:
   ```bash
   uv sync
   ```
3. Создайте файл `.env` на основе `.env.example`.

## 🏃 Запуск

Нужны **два терминала**.

**Бэкенд** — `http://localhost:8000`, документация Swagger: `/docs`

```bash
uv run uvicorn app.main:app --reload
```

**Фронтенд** — `http://localhost:8501`

```bash
uv run streamlit run frontend/app.py
```

Запускайте Streamlit из **корня репозитория**. Файл `frontend/.streamlit/config.toml` задаёт ограничения на размер загрузки в UI.

## 📁 Структура проекта

```text
.
├── app/                 # приложение FastAPI
│   ├── main.py
│   ├── lifespan.py
│   ├── db.py
│   ├── dependencies.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── images.py
│   ├── s3_storage.py
│   └── users.py
├── docs/                # README (KK, RU) и скриншоты
│   ├── README_KK.md
│   ├── README_RU.md
│   └── images/
├── frontend/
│   ├── app.py
│   └── .streamlit/
├── pyproject.toml
├── uv.lock
└── .env
```
