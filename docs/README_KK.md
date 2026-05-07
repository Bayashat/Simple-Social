# 📸 Simple Social

[ 🇬🇧 English ](../README.md) | [ 🇰🇿 Қазақша ](README_KK.md) | [ 🇷🇺 Русский ](README_RU.md)

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![uv](https://img.shields.io/badge/uv-басқарылатын-purple.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688.svg?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-389776.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-веб_UI-FF4B4B.svg?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-дерекқор-003B57.svg?logo=sqlite&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-Async_ORM-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/fastapi--users-JWT-black.svg)
![ImageKit](https://img.shields.io/badge/ImageKit-CDN-000000.svg)
![AWS_S3](https://img.shields.io/badge/AWS-S3_FF9900.svg?logo=amazons3&logoColor=white)
![Boto3](https://img.shields.io/badge/boto3-SDK-232F3E.svg?logo=amazon-aws&logoColor=white)

**FastAPI** бэкенді мен **Streamlit** веб интерфейсі бар жеңіл «әлеуметтік» қосымша.

> **Екі Storage-ды толық қолдау:** бэкенд пен UI **ImageKit пен AWS S3 екеуін де** қолдайды. Әр жүктеуде бір нысан таңдалады (**ImageKit** — CDN және түрлендіру; **S3** — өз бакетіңізде). Басты бетте ImageKit үшін URL түрлендіріледі; S3 сілтемелері өз қалпында қалады.

## 🚀 Мүмкіндіктері

- **Аутентификация:** JWT арқылы тіркеу және кіру (`fastapi-users`).
- **Медиа:** Сурет, бейне және файлдар (MIME бойынша PDF, HTML, т.б.).
- **Екі объектілік қойма:** **ImageKit немесе AWS S3** — `.env` екеуін де баптаңыз.
- **Басты бет:** Хронология, жазбаны өшіру батырмасы бар; әр жолда **Storage:** ImageKit / AWS S3.
- **Түрлендіру:** Тек `storage=imagekit` жазбалары үшін мәтін қабатын URL арқылы қосады.

## 📷 скриншоттар

| Жүктеу беті | Басты бет |
|:--:|:--:|
| ![Upload page](./images/upload_page.png) | ![Feed page](./images/feed_page.png) |

## ⚙️ Баптау

1. Репозиторийді алып, жобаның түбіріне өтіңіз.
2. Dependenci-ларды орнату:
   ```bash
   uv sync
   ```
3. Түбірде `.env.example` файлына сәйкес `.env` файлын құрыңыз.

## 🏃 Іске қосу

**Екі терминал қажет.**

**Бэкенд** — `http://localhost:8000`, құжаттама — `/docs`

```bash
uv run uvicorn app.main:app --reload
```

**Фронтенд** — `http://localhost:8501`

```bash
uv run streamlit run frontend/app.py
```

Стримлитті **репо түбірінен** іске қосыңыз. `frontend/.streamlit/config.toml` жүктеу шегін көрсете алады.

## 📁 Проект құрылымы

```text
.
├── app/                 # FastAPI
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
├── docs/                # README (KK, RU) және скриншоттар
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
