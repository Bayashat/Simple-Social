from app.api.deps import fastapi_users
from app.schemas import UserRead, UserUpdate

router = fastapi_users.get_users_router(UserRead, UserUpdate)
