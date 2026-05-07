from app.api.deps import fastapi_users
from app.core.auth import auth_backend
from app.schemas import UserCreate, UserRead

jwt_router = fastapi_users.get_auth_router(auth_backend)

register_router = fastapi_users.get_register_router(UserRead, UserCreate)

reset_password_router = fastapi_users.get_reset_password_router()

verify_router = fastapi_users.get_verify_router(UserRead)
