from fastapi import FastAPI

from app.api.routers import auth, posts
from app.api.routers import users as users_router
from app.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(auth.jwt_router, prefix="/auth/jwt", tags=["auth"])
app.include_router(auth.register_router, prefix="/auth", tags=["auth"])
app.include_router(auth.reset_password_router, prefix="/auth", tags=["auth"])
app.include_router(auth.verify_router, prefix="/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/users", tags=["users"])

app.include_router(posts.router)
