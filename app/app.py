from fastapi import FastAPI

app = FastAPI(
    title="Blog API",
    description="A FastAPI based blog application",
    version="0.1.0",
    contact={
        "name": "Bayashat Tokmukamet",
        "email": "bayashat.tokmukamet@gmail.com",
    },
    license={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

